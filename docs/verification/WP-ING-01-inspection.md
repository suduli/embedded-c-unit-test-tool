# Verification Inspection Note — WP-ING-01 (Compilation Database Ingestion)

Inspection evidence for requirements verified by documentation (*D*) under WP-ING-01:

| Requirement ID | Summary Statement | Implementation Reference | Verification Evidence |
|---|---|---|---|
| **TOOL-ING-040** | Document and support generating a compilation database via CMake (`CMAKE_EXPORT_COMPILE_COMMANDS=ON`) as the recommended path | `src/ectt/ing/cmake.py` (`generate_compdb_via_cmake`, `CMAKE_EXPORT_DOCUMENTATION`) | `src/ectt/ing/cmake.py` documents the recommended CMake invocation (`cmake -S <src> -B <build> -DCMAKE_EXPORT_COMPILE_COMMANDS=ON`) and generator guidelines. `tests/ing/test_cmake.py::test_cmake_documentation_presence` and `test_cmake_scratch_configure_happy_path` prove scratch-configure compilation database generation without modifying user source or `CMakeLists.txt`. |
