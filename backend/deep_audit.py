
import ast
import os
import sys

class BugFinder(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.errors = []
        self.defined_names = set(dir(__builtins__))
        self.defined_names.add('__file__')
        self.defined_names.add('__name__')
        
    def visit_Import(self, node):
        for alias in node.names:
            self.defined_names.add(alias.asname or alias.name.split('.')[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.defined_names.add(alias.asname or alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        # Add function arguments to defined names for this scope
        # This is a naive scope check; robust scoping requires a symbol table
        local_defined = self.defined_names.copy()
        for arg in node.args.args:
            local_defined.add(arg.arg)
        if node.args.vararg:
            local_defined.add(node.args.vararg.arg)
        if node.args.kwarg:
            local_defined.add(node.args.kwarg.arg)
            
        # Temporarily use local scope
        outer_defined = self.defined_names
        self.defined_names = local_defined
        
        # Check for unawaited coroutines (heuristics)
        self.check_unawaited(node)
        
        self.generic_visit(node)
        
        # Restore outer scope
        self.defined_names = outer_defined
        self.defined_names.add(node.name)

    def visit_AsyncFunctionDef(self, node):
        # Same as FunctionDef but for async
        self.visit_FunctionDef(node)

    def visit_ClassDef(self, node):
        self.defined_names.add(node.name)
        self.generic_visit(node)

    def visit_Assign(self, node):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.defined_names.add(target.id)
            elif isinstance(target, ast.Tuple):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.defined_names.add(elt.id)
        self.generic_visit(node)
        
    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Store):
            self.defined_names.add(node.id)
        # Naive check: if loading and not in defined_names, might be undefined
        # Disabled for now as naive scoping is too noisy
        # elif isinstance(node.ctx, ast.Load) and node.id not in self.defined_names:
        #     self.errors.append(f"Line {node.lineno}: Possible undefined variable '{node.id}'")

    def check_unawaited(self, node):
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Attribute):
                    # Check for common async methods called without await
                    name = child.func.attr
                    if name in ['process', 'generate', 'ainvoke', 'astream'] and 'async' in self.filename:
                         # This is a weak heuristic, real check needs type inference
                         pass

def check_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            code = f.read()
        tree = ast.parse(code)
    except Exception as e:
        print(f"Syntax Error in {filepath}: {e}")
        return

    # Check 1: coroutines without await (simple text grep for now as AST is complex)
    lines = code.split('\n')
    for i, line in enumerate(lines):
        if 'async def' in line:
            continue
        # Look for calls to known async methods that are NOT awaited
        if any(x in line for x in ['.generate(', '.process(', '.run_']) and 'await ' not in line and 'def ' not in line:
             # Exclude definitions and comments
            if not line.strip().startswith('#'):
                 # Heuristic: these are likely async methods in this codebase
                print(f"{filepath}:{i+1}: Warning - Potential unawaited async call: {line.strip()}")
        
        # Look for missing variables (simple heuristic for bugs like 'en_prompt')
        if "name '" in line and "' is not defined" in line:
             # logic for runtime log analysis, not static code
             pass

def analyze_directory(directory):
    print(f"Scanning {directory}...")
    for root, _, files in os.walk(directory):
        if 'venv' in root or '__pycache__' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                check_file(os.path.join(root, file))

if __name__ == "__main__":
    analyze_directory(r"C:\Users\rahul\Documents\GitHub\Legal-Ops\backend")
