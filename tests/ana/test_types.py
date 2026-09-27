# implements: DSN-ANA-020
"""Tests for transitive type closure and deterministic type ID extraction (CMP-ANA).

Verifies: TOOL-PAR-040, TOOL-NFR-060, DSN-ANA-020.
"""

from __future__ import annotations

import os
from pathlib import Path

from ectt.ana.frontend import parse
from ectt.ana.interface import extract_interfaces
from ectt.ana.model import AnalysisUnit


def test_anonymous_typedef_struct_extraction() -> None:
    """verifies: TOOL-PAR-040, DSN-ANA-020"""
    code = b"""
    typedef struct {
        float u;
        float v;
    } Vec2;

    Vec2 compute_vec(Vec2 input) {
        Vec2 res = input;
        return res;
    }
    """
    ptu = parse("anon.c", args=["-std=c99"], unsaved_files=[("anon.c", code)])
    unit = extract_interfaces(ptu)

    assert len(unit.functions) == 1
    fn = unit.functions[0]
    assert fn.return_type == "ref:type.Vec2"
    assert fn.parameters[0].type == "ref:type.Vec2"

    types = unit.types
    # Typedef Vec2 entry
    assert "type.Vec2" in types
    vec2_type = types["type.Vec2"]
    assert vec2_type.kind == "typedef"
    assert vec2_type.name == "Vec2"
    assert vec2_type.underlying_type is not None
    assert vec2_type.underlying_type.startswith("ref:type.anon.struct.Vec2_")

    # Underlying anonymous struct entry
    anon_key = vec2_type.underlying_type.removeprefix("ref:")
    assert anon_key in types
    anon_struct = types[anon_key]
    assert anon_struct.kind == "struct"
    assert anon_struct.is_anonymous is True
    assert len(anon_struct.members) == 2
    member_names = [m.name for m in anon_struct.members]
    assert member_names == ["u", "v"]
    assert anon_struct.members[0].type == "ref:type.float"
    assert anon_struct.members[1].type == "ref:type.float"


def test_self_referential_struct_closure_terminates() -> None:
    """verifies: TOOL-PAR-040, DSN-ANA-020"""
    code = b"""
    struct Node {
        int value;
        struct Node *next;
        struct Node *prev;
    };

    struct Node *get_head(struct Node *list) {
        return list;
    }
    """
    ptu = parse("list.c", args=["-std=c99"], unsaved_files=[("list.c", code)])
    unit = extract_interfaces(ptu)

    types = unit.types
    assert "type.struct.Node" in types
    node_type = types["type.struct.Node"]
    assert node_type.kind == "struct"
    assert node_type.name == "Node"
    assert len(node_type.members) == 3

    m_map = {m.name: m.type for m in node_type.members}
    assert m_map["value"] == "ref:type.int"
    assert m_map["next"] == "ref:type.ptr.struct.Node"
    assert m_map["prev"] == "ref:type.ptr.struct.Node"

    # Pointer entry
    assert "type.ptr.struct.Node" in types
    ptr_node = types["type.ptr.struct.Node"]
    assert ptr_node.kind == "pointer"
    assert ptr_node.target == "ref:type.struct.Node"
    assert ptr_node.is_const is False


def test_nested_union_and_enum_transitivity() -> None:
    """verifies: TOOL-PAR-040, DSN-ANA-020"""
    code = b"""
    enum Status {
        STATUS_OK = 0,
        STATUS_ERR = 1
    };

    union DataPayload {
        int raw_int;
        float raw_float;
        enum Status status_val;
    };

    struct Packet {
        int id;
        union DataPayload payload;
    };

    void process_packet(struct Packet pkt) {
    }
    """
    ptu = parse("nested.c", args=["-std=c99"], unsaved_files=[("nested.c", code)])
    unit = extract_interfaces(ptu)

    types = unit.types

    # Top-level struct
    assert "type.struct.Packet" in types
    pkt_type = types["type.struct.Packet"]
    assert pkt_type.kind == "struct"

    # Transitive union
    assert "type.union.DataPayload" in types
    union_type = types["type.union.DataPayload"]
    assert union_type.kind == "union"
    assert union_type.name == "DataPayload"
    u_members = {m.name: m.type for m in union_type.members}
    assert u_members["raw_int"] == "ref:type.int"
    assert u_members["raw_float"] == "ref:type.float"
    assert u_members["status_val"] == "ref:type.enum.Status"

    # Transitive enum reached through union member
    assert "type.enum.Status" in types
    enum_type = types["type.enum.Status"]
    assert enum_type.kind == "enum"
    assert enum_type.name == "Status"
    enum_vals = {e.name: e.value for e in enum_type.enumerators}
    assert enum_vals == {"STATUS_OK": 0, "STATUS_ERR": 1}


def test_header_declared_type_transitivity() -> None:
    """verifies: TOOL-PAR-040, DSN-ANA-020"""
    hdr_code = b"""
    #ifndef SENSOR_HDR_H
    #define SENSOR_HDR_H

    typedef unsigned short sensor_raw_t;

    struct SensorConfig {
        sensor_raw_t threshold;
        int flags;
    };

    #endif
    """
    main_code = b"""
    #include "sensor_hdr.h"

    int configure_sensor(struct SensorConfig *cfg) {
        return cfg ? (int)cfg->threshold : -1;
    }
    """
    cur = os.path.abspath(".")
    hdr_path = os.path.join(cur, "sensor_hdr.h")

    ptu = parse(
        "sensor.c",
        args=["-std=c99", f"-I{cur}"],
        unsaved_files=[(hdr_path, hdr_code), ("sensor.c", main_code)],
    )
    unit = extract_interfaces(ptu)

    types = unit.types

    # Struct defined in header
    assert "type.struct.SensorConfig" in types
    cfg_type = types["type.struct.SensorConfig"]
    assert cfg_type.kind == "struct"
    assert cfg_type.location is not None
    assert "sensor_hdr.h" in cfg_type.location.file
    assert cfg_type.location.origin == "include"

    # Typedef defined in header
    assert "type.sensor_raw_t" in types
    td_type = types["type.sensor_raw_t"]
    assert td_type.kind == "typedef"
    assert td_type.location is not None
    assert "sensor_hdr.h" in td_type.location.file
    assert td_type.location.origin == "include"
    assert td_type.underlying_type == "ref:type.unsigned_short"


def test_determinism_across_parses() -> None:
    """verifies: TOOL-PAR-040, TOOL-NFR-060, DSN-ANA-020"""
    code = b"""
    typedef struct {
        int x;
        int y;
    } Point;

    enum Flag { F_NONE, F_ACTIVE };

    int g_counter = 0;

    Point calculate(Point pt, enum Flag f) {
        g_counter++;
        Point res = pt;
        return res;
    }
    """
    # Parse and extract run 1
    ptu1 = parse("det.c", args=["-std=c99"], unsaved_files=[("det.c", code)])
    unit1 = extract_interfaces(ptu1)
    json1 = unit1.to_json()

    # Parse and extract run 2
    ptu2 = parse("det.c", args=["-std=c99"], unsaved_files=[("det.c", code)])
    unit2 = extract_interfaces(ptu2)
    json2 = unit2.to_json()

    # Byte-identical canonical JSON serialization
    assert json1 == json2
    assert len(json1) > 0


def test_bitfield_members_extracted() -> None:
    """verifies: TOOL-PAR-040, DSN-ANA-020"""
    code = b"""
    struct BitfieldReg {
        unsigned int enable : 1;
        unsigned int mode : 3;
        unsigned int priority : 4;
    };

    void write_reg(struct BitfieldReg r) {}
    """
    ptu = parse("reg.c", args=["-std=c99"], unsaved_files=[("reg.c", code)])
    unit = extract_interfaces(ptu)

    assert "type.struct.BitfieldReg" in unit.types
    reg_type = unit.types["type.struct.BitfieldReg"]
    assert len(reg_type.members) == 3

    m_map = {m.name: m.bit_width for m in reg_type.members}
    assert m_map["enable"] == 1
    assert m_map["mode"] == 3
    assert m_map["priority"] == 4


def test_function_pointer_parameters_and_types() -> None:
    """verifies: TOOL-PAR-030, TOOL-PAR-040, DSN-ANA-020"""
    code = b"""
    typedef int (*named_cb_t)(int code, const char *msg);

    void register_handlers(
        named_cb_t primary_cb,
        void (*fallback_cb)(double val)
    ) {}
    """
    ptu = parse("fp.c", args=["-std=c99"], unsaved_files=[("fp.c", code)])
    unit = extract_interfaces(ptu)

    types = unit.types
    # Named callback typedef
    assert "type.named_cb_t" in types
    td = types["type.named_cb_t"]
    assert td.kind == "typedef"
    assert td.underlying_type is not None

    # Underlying function pointer
    fn_ptr_key = td.underlying_type.removeprefix("ref:")
    assert fn_ptr_key in types
    fn_ptr = types[fn_ptr_key]
    assert fn_ptr.kind == "function_pointer"
    assert fn_ptr.return_type == "ref:type.int"
    assert len(fn_ptr.parameters) == 2

    # Anonymous inline function pointer parameter fallback_cb
    fn = unit.functions[0]
    fallback_param = fn.parameters[1]
    assert fallback_param.name == "fallback_cb"
    assert fallback_param.direction == "unknown"
    fallback_key = fallback_param.type.removeprefix("ref:")
    assert fallback_key in types
    fallback_type = types[fallback_key]
    assert fallback_type.kind == "function_pointer"
    assert fallback_type.return_type == "ref:type.void"


def test_out_of_tree_include_determinism_across_root_directories(tmp_path: Path) -> None:
    """verifies: TOOL-PAR-040, TOOL-NFR-060, TOOL-NFR-070, TOOL-NFR-080, DSN-ANA-020"""
    # Create two different absolute root directories to verify machine-independence
    root1 = tmp_path / "checkout_a"
    root2 = tmp_path / "checkout_b"

    sdk_hdr_content = (
        "#ifndef SDK_DEVICE_H\n"
        "#define SDK_DEVICE_H\n"
        "\n"
        "typedef struct {\n"
        "    int baudrate;\n"
        "    int timeout_ms;\n"
        "} sdk_config_t;\n"
        "\n"
        "struct SdkDevice {\n"
        "    sdk_config_t cfg;\n"
        "    int status;\n"
        "};\n"
        "\n"
        "#endif\n"
    )

    main_c_content = (
        "#include \"sdk_device.h\"\n"
        "\n"
        "int init_device(struct SdkDevice *dev, const sdk_config_t *cfg) {\n"
        "    if (!dev || !cfg) return -1;\n"
        "    dev->cfg = *cfg;\n"
        "    dev->status = 1;\n"
        "    return 0;\n"
        "}\n"
    )

    # Setup tree in root1
    sdk_dir1 = root1 / "sdk" / "include"
    sdk_dir1.mkdir(parents=True)
    (sdk_dir1 / "sdk_device.h").write_text(sdk_hdr_content, encoding="utf-8")
    proj_dir1 = root1 / "proj"
    src_dir1 = proj_dir1 / "src"
    src_dir1.mkdir(parents=True)
    src_file1 = src_dir1 / "main.c"
    src_file1.write_text(main_c_content, encoding="utf-8")

    # Setup identical tree in root2
    sdk_dir2 = root2 / "sdk" / "include"
    sdk_dir2.mkdir(parents=True)
    (sdk_dir2 / "sdk_device.h").write_text(sdk_hdr_content, encoding="utf-8")
    proj_dir2 = root2 / "proj"
    src_dir2 = proj_dir2 / "src"
    src_dir2.mkdir(parents=True)
    src_file2 = src_dir2 / "main.c"
    src_file2.write_text(main_c_content, encoding="utf-8")

    # Parse and extract from root1
    ptu1 = parse(
        str(src_file1),
        args=["-std=c99", f"-I{sdk_dir1.resolve()}"],
        working_directory=str(proj_dir1),
    )
    unit1 = extract_interfaces(ptu1, working_directory=str(proj_dir1))
    json1 = unit1.to_json()

    # Parse and extract from root2
    ptu2 = parse(
        str(src_file2),
        args=["-std=c99", f"-I{sdk_dir2.resolve()}"],
        working_directory=str(proj_dir2),
    )
    unit2 = extract_interfaces(ptu2, working_directory=str(proj_dir2))
    json2 = unit2.to_json()

    # 1. Byte-identical canonical JSON serialization across disparate checkout directories
    assert json1 == json2

    # 2. Assert no absolute machine paths leaked into the serialized model
    assert str(root1.resolve()).replace("\\", "/") not in json1
    assert str(root2.resolve()).replace("\\", "/") not in json2
    assert str(sdk_dir1.resolve()).replace("\\", "/") not in json1
    assert str(sdk_dir2.resolve()).replace("\\", "/") not in json2

    # 3. Assert origin markers and relative paths for out-of-tree and in-tree types
    types = unit1.types
    assert "type.sdk_config_t" in types
    cfg_td = types["type.sdk_config_t"]
    assert cfg_td.location is not None
    assert cfg_td.location.file == "sdk_device.h"
    assert cfg_td.location.origin == "include"

    assert "type.struct.SdkDevice" in types
    dev_struct = types["type.struct.SdkDevice"]
    assert dev_struct.location is not None
    assert dev_struct.location.file == "sdk_device.h"
    assert dev_struct.location.origin == "include"

    # Anonymous struct for sdk_config_t
    anon_key = cfg_td.underlying_type.removeprefix("ref:")
    assert anon_key in types
    anon_struct = types[anon_key]
    assert anon_struct.location is not None
    assert anon_struct.location.file == "sdk_device.h"
    assert anon_struct.location.origin == "include"

    # Function in project main.c
    fn = unit1.functions[0]
    assert fn.location.file == "src/main.c"
    assert fn.location.origin == "project"
