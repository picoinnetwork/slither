"""
    Module printing summary of the contract
"""
from pathlib import Path
from slither.printers.abstract_printer import AbstractPrinter
from slither.utils.myprettytable import transpose, make_pretty_table
from slither.utils.tests_pattern import is_test_file


# @param takes a list of lines and returns a tuple of (cloc, sloc, loc)
def count_lines(contract_lines: list) -> tuple:
    multiline_comment = False
    cloc = 0
    sloc = 0
    loc = 0

    for line in contract_lines:
        loc += 1
        stripped_line = line.strip()
        if not multiline_comment:
            if stripped_line.startswith("//"):
                cloc += 1
            elif "/*" in stripped_line:
                # Account for case where /* is followed by */ on the same line.
                # If it is, then multiline_comment does not need to be set to True
                start_idx = stripped_line.find("/*")
                end_idx = stripped_line.find("*/", start_idx + 2)
                if end_idx == -1:
                    multiline_comment = True
                cloc += 1
            elif stripped_line:
                sloc += 1
        else:
            cloc += 1
            if "*/" in stripped_line:
                multiline_comment = False

    return cloc, sloc, loc


def _update_lines_dict(file_type: str, lines: list, lines_dict: dict) -> dict:
    cloc, sloc, loc = count_lines(lines)
    lines_dict[file_type]["loc"] += loc
    lines_dict[file_type]["cloc"] += cloc
    lines_dict[file_type]["sloc"] += sloc
    return lines_dict


# takes a Slither object and returns a dict of loc metrics:
# {
#     "src" : {"loc": 30, "sloc": 20, "cloc":  5},   # code in source files
#     "dep" : {"loc": 50, "sloc": 30, "cloc": 10},   # code in dependencies
#     "test": {"loc": 80, "sloc": 60, "cloc": 10},   # code in tests
# }
# * sloc = source lines of code, cloc = comment lines of code, loc = all lines of code
def compute_loc_metrics(slither) -> dict:
    lines_dict = {
        "src": {"loc": 0, "sloc": 0, "cloc": 0},
        "dep": {"loc": 0, "sloc": 0, "cloc": 0},
        "test": {"loc": 0, "sloc": 0, "cloc": 0},
    }

    if not slither.source_code:
        return lines_dict

    for filename, source_code in slither.source_code.items():
        current_lines = source_code.splitlines()
        is_dep = False
        if slither.crytic_compile:
            is_dep = slither.crytic_compile.is_dependency(filename)
        file_type = "dep" if is_dep else "test" if is_test_file(Path(filename)) else "src"
        lines_dict = _update_lines_dict(file_type, current_lines, lines_dict)
    return lines_dict


class Loc(AbstractPrinter):
    ARGUMENT = "loc"
    HELP = """Count the total number lines of code (LOC), source lines of code (SLOC), \
            and comment lines of code (CLOC) found in source files (SRC), dependencies (DEP), \
            and test files (TEST)."""

    WIKI = "https://github.com/trailofbits/slither/wiki/Printer-documentation#loc"

    def output(self, _filename):
        # compute loc metrics
        lines_dict = compute_loc_metrics(self.slither)

        # prepare the table
        headers = [""] + list(lines_dict.keys())
        report_dict = transpose(lines_dict)
        table = make_pretty_table(headers, report_dict)
        txt = "Lines of Code \n" + str(table)
        self.info(txt)
        res = self.generate_output(txt)
        res.add_pretty_table(table, "Code Lines")
        return res