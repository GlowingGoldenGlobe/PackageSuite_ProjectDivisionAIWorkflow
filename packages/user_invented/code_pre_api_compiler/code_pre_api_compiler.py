#!/usr/bin/env python3
"""
Code Pre-API Compiler Package
Compiles code to reduce tokens before API submission

Features:
- Remove unnecessary whitespace
- Remove line breaks where safe
- Remove comments
- Summarize README files
- Option to compile to bytecode
- Mirror project folder structure
"""
import os
import re
import ast
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional


class CodePreAPICompiler:
    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.stats = {
            'files_processed': 0,
            'original_size': 0,
            'compiled_size': 0,
            'tokens_saved': 0
        }
        
    def compile_project(self, 
                       include_all_files: bool = False,
                       compile_to_bytes: bool = False,
                       preserve_structure: bool = True):
        """Main compilation process"""
        print(f"Compiling project from: {self.source_dir}")
        print(f"Output directory: {self.output_dir}")
        
        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process files
        for file_path in self._get_files_to_process(include_all_files):
            self._process_file(file_path, compile_to_bytes, preserve_structure)
            
        # Generate summary
        self._generate_summary()
        
    def _get_files_to_process(self, include_all: bool) -> List[Path]:
        """Get list of files to process"""
        extensions = ['.py', '.js', '.java', '.cpp', '.c', '.h']
        if include_all:
            extensions.extend(['.md', '.txt', '.json', '.yaml', '.yml'])
            
        files = []
        for ext in extensions:
            files.extend(self.source_dir.rglob(f"*{ext}"))
            
        # Filter out common excludes
        excludes = ['__pycache__', '.git', 'node_modules', 'venv', '.env']
        files = [f for f in files if not any(ex in str(f) for ex in excludes)]
        
        return files
        
    def _process_file(self, file_path: Path, compile_to_bytes: bool, preserve_structure: bool):
        """Process individual file"""
        relative_path = file_path.relative_to(self.source_dir)
        
        if preserve_structure:
            output_path = self.output_dir / relative_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = self.output_dir / file_path.name
            
        # Read original content
        try:
            original_content = file_path.read_text(encoding='utf-8')
            self.stats['original_size'] += len(original_content)
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return
            
        # Apply compilation based on file type
        if file_path.suffix == '.py':
            compiled_content = self._compile_python(original_content)
        elif file_path.suffix in ['.js', '.java', '.cpp', '.c']:
            compiled_content = self._compile_code(original_content)
        elif file_path.suffix in ['.md', '.txt']:
            compiled_content = self._compile_docs(original_content)
        else:
            compiled_content = original_content
            
        # Write compiled content
        if compile_to_bytes and file_path.suffix == '.py':
            # Compile to Python bytecode
            import py_compile
            output_path = output_path.with_suffix('.pyc')
            try:
                py_compile.compile(file_path, output_path, doraise=True)
            except Exception as e:
                print(f"Bytecode compilation failed for {file_path}: {e}")
                output_path = output_path.with_suffix('.py')
                output_path.write_text(compiled_content)
        else:
            output_path.write_text(compiled_content)
            
        self.stats['compiled_size'] += len(compiled_content)
        self.stats['files_processed'] += 1
        
    def _compile_python(self, content: str) -> str:
        """Compile Python code"""
        # Remove comments but preserve docstrings
        lines = content.split('\n')
        compiled_lines = []
        in_docstring = False
        docstring_char = None
        
        for line in lines:
            stripped = line.strip()
            
            # Handle docstrings
            if '"""' in line or "'''" in line:
                if not in_docstring:
                    in_docstring = True
                    docstring_char = '"""' if '"""' in line else "'''"
                    compiled_lines.append(line)
                elif docstring_char in line:
                    in_docstring = False
                    compiled_lines.append(line)
                    docstring_char = None
                else:
                    compiled_lines.append(line)
            elif in_docstring:
                compiled_lines.append(line)
            elif stripped.startswith('#'):
                # Skip comments unless they're directives
                if stripped.startswith('#!') or 'coding:' in stripped:
                    compiled_lines.append(line)
            else:
                # Remove inline comments
                if '#' in line:
                    code_part = line.split('#')[0].rstrip()
                    if code_part:
                        compiled_lines.append(code_part)
                else:
                    if stripped:  # Only add non-empty lines
                        compiled_lines.append(line.rstrip())
                        
        # Join and remove excessive blank lines
        compiled = '\n'.join(compiled_lines)
        compiled = re.sub(r'\n\n\n+', '\n\n', compiled)
        
        # Minimize whitespace in safe places
        compiled = self._minimize_whitespace(compiled)
        
        return compiled.strip()
        
    def _compile_code(self, content: str) -> str:
        """Compile general code (JS, Java, C++)"""
        # Remove single-line comments
        content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
        
        # Remove multi-line comments
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r' +', ' ', content)
        
        return content.strip()
        
    def _compile_docs(self, content: str) -> str:
        """Compile documentation files"""
        lines = content.split('\n')
        
        # For README files, create summary
        if 'readme' in content.lower()[:100]:
            # Extract title and main sections
            summary_lines = []
            for line in lines[:20]:  # First 20 lines usually contain overview
                if line.strip() and not line.startswith('<!--'):
                    summary_lines.append(line)
                    
            return '\n'.join(summary_lines[:10])  # Keep first 10 meaningful lines
        else:
            # For other docs, remove excessive blank lines
            return re.sub(r'\n\n\n+', '\n\n', content).strip()
            
    def _minimize_whitespace(self, content: str) -> str:
        """Minimize whitespace while preserving code structure"""
        # Remove trailing whitespace
        lines = [line.rstrip() for line in content.split('\n')]
        
        # Remove space around operators where safe
        safe_operators = ['=', '+=', '-=', '*=', '/=', '==', '!=', '<=', '>=']
        for op in safe_operators:
            # Only in assignments and comparisons, not in strings
            lines = [re.sub(f' {re.escape(op)} ', op, line) 
                    if '"' not in line and "'" not in line else line 
                    for line in lines]
                    
        return '\n'.join(lines)
        
    def _generate_summary(self):
        """Generate compilation summary"""
        reduction = (1 - self.stats['compiled_size'] / max(self.stats['original_size'], 1)) * 100
        
        # Estimate token savings (rough estimate: 1 token ≈ 4 characters)
        self.stats['tokens_saved'] = (self.stats['original_size'] - self.stats['compiled_size']) // 4
        
        summary = {
            'compilation_stats': self.stats,
            'reduction_percentage': round(reduction, 2),
            'source_directory': str(self.source_dir),
            'output_directory': str(self.output_dir)
        }
        
        # Write summary
        summary_path = self.output_dir / 'compilation_summary.json'
        summary_path.write_text(json.dumps(summary, indent=2))
        
        print(f"\n✓ Compilation complete!")
        print(f"  Files processed: {self.stats['files_processed']}")
        print(f"  Size reduction: {reduction:.1f}%")
        print(f"  Estimated tokens saved: {self.stats['tokens_saved']:,}")
        

def main():
    """CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Code Pre-API Compiler')
    parser.add_argument('source', help='Source directory')
    parser.add_argument('output', help='Output directory')
    parser.add_argument('--all-files', action='store_true', 
                       help='Include all file types')
    parser.add_argument('--bytecode', action='store_true',
                       help='Compile Python to bytecode')
    parser.add_argument('--no-structure', action='store_true',
                       help='Don\'t preserve directory structure')
    
    args = parser.parse_args()
    
    compiler = CodePreAPICompiler(args.source, args.output)
    compiler.compile_project(
        include_all_files=args.all_files,
        compile_to_bytes=args.bytecode,
        preserve_structure=not args.no_structure
    )
    

if __name__ == '__main__':
    main()