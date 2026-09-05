import textwrap

from clang.cindex import Index

from extract import extract_translation_unit, parse_args_for


def test_parse_args_targets_arm_bare_metal():
    args = parse_args_for("dummy.c", fixture_root="/fake/fixture")
    assert "-target" in args
    idx = args.index("-target")
    assert args[idx + 1] == "thumbv7em-none-eabi"
    assert "-DSTM32F407xx" in args
    assert any(a.startswith("-I") and "CMSIS" in a for a in args)


def _parse(source: str):
    index = Index.create()
    tu = index.parse(
        "test.c", args=["-target", "thumbv7em-none-eabi", "-std=c11"],
        unsaved_files=[("test.c", source)],
    )
    return tu


def test_extracts_function_signature():
    tu = _parse("int add(int a, int b) { return a + b; }")
    result = extract_translation_unit(tu)
    assert len(result.functions) == 1
    fn = result.functions[0]
    assert fn.name == "add"
    assert fn.return_type == "int"
    assert fn.params == [("int", "a"), ("int", "b")]
    assert fn.is_static is False


def test_extracts_static_function():
    tu = _parse("static void helper(void) {}")
    result = extract_translation_unit(tu)
    assert result.functions[0].is_static is True


def test_extracts_nested_struct_type():
    src = textwrap.dedent("""
        typedef struct {
            struct { unsigned char r, g, b; } color;
            int id;
        } Widget_t;
    """)
    tu = _parse(src)
    result = extract_translation_unit(tu)
    names = [t.name for t in result.types]
    assert "Widget_t" in names


def test_extracts_global_variable():
    tu = _parse("volatile int counter;")
    result = extract_translation_unit(tu)
    assert len(result.globals) == 1
    assert result.globals[0].name == "counter"


def test_direct_call_is_resolved():
    src = "void a(void) {} void b(void) { a(); }"
    tu = _parse(src)
    result = extract_translation_unit(tu)
    assert ("b", "a") in result.direct_calls
    assert result.indirect_calls == []


def test_indirect_call_through_function_pointer_is_flagged():
    src = textwrap.dedent("""
        typedef void (*handler_t)(int);
        void dispatch(handler_t h) { h(1); }
    """)
    tu = _parse(src)
    result = extract_translation_unit(tu)
    assert result.direct_calls == []
    assert len(result.indirect_calls) == 1
    assert result.indirect_calls[0].caller == "dispatch"
