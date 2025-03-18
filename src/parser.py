import ast
import os
import csv
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path

@dataclass
class OdooField:
    name: str
    field_type: str
    required: bool = False
    related_model: Optional[str] = None
    string: Optional[str] = None
    default: Any = None
    compute: Optional[str] = None
    store: bool = True
    readonly: bool = False
    inverse: Optional[str] = None
    index: bool = False
    tracking: bool = False
    help: Optional[str] = None
    
@dataclass
class OdooMethod:
    name: str
    decorators: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    complexity: int = 0  # Cyclomatic complexity
    line_count: int = 0
    docstring: Optional[str] = None
    api_depends: List[str] = field(default_factory=list)
    is_constraint: bool = False
    is_compute: bool = False
    is_onchange: bool = False
    
@dataclass
class OdooModel:
    name: str
    inherit: List[str] = field(default_factory=list)
    description: str = ""
    fields: Dict[str, OdooField] = field(default_factory=dict)
    methods: Dict[str, OdooMethod] = field(default_factory=dict)
    order: Optional[str] = None
    record_name: Optional[str] = None
    constraints: List[str] = field(default_factory=list)
    
@dataclass
class OdooView:
    name: str
    model: str
    type: str
    arch: str
    inherit_id: Optional[str] = None
    priority: int = 16
    field_names: List[str] = field(default_factory=list)

@dataclass
class SecurityRule:
    name: str
    model_id: str
    groups: List[str]
    perm_read: bool = False
    perm_write: bool = False
    perm_create: bool = False
    perm_unlink: bool = False
    domain_force: Optional[str] = None
    
@dataclass
class OdooMenuItem:
    id: str
    name: str
    parent_id: Optional[str] = None
    action: Optional[str] = None
    sequence: int = 10
    groups: List[str] = field(default_factory=list)

class OdooModuleParser:
    def __init__(self, module_path: str):
        self.module_path = Path(module_path)
        self.models: Dict[str, OdooModel] = {}
        self.views: Dict[str, OdooView] = {}
        self.security_rules: Dict[str, SecurityRule] = {}
        self.menu_items: Dict[str, OdooMenuItem] = {}
        self.manifest: Dict = {}
        self.model_dependencies: Dict[str, Set[str]] = {}
        self.field_dependencies: Dict[str, Set[Tuple[str, str]]] = {}  # model -> [(field, dependency), ...]
        
    def parse_module(self):
        """Parse the entire Odoo module"""
        self._parse_manifest()
        self._parse_models()
        self._parse_views()
        self._parse_security()
        self._parse_menus()
        self._analyze_dependencies()
        
    def _parse_manifest(self):
        """Parse the __manifest__.py file"""
        manifest_path = self.module_path / '__manifest__.py'
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Remove comments to avoid parsing errors
                    content = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
                    try:
                        self.manifest = ast.literal_eval(content)
                    except (SyntaxError, ValueError):
                        print(f"Warning: Could not parse manifest file {manifest_path}")
                        self.manifest = {}
            except Exception as e:
                print(f"Error reading manifest file: {e}")
                self.manifest = {}
                
    def _parse_models(self):
        """Parse all Python model files"""
        models_dir = self.module_path / 'models'
        if models_dir.exists():
            for file_path in models_dir.glob('*.py'):
                if file_path.name != '__init__.py':
                    self._parse_model_file(file_path)
                    
    def _parse_model_file(self, file_path: Path):
        """Parse a single model file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            # First pass: collect all models
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if self._is_odoo_model(node):
                        model = self._extract_model_info(node)
                        if model.name:  # Only add if model has a name
                            self.models[model.name] = model
                            
            # Second pass: extract methods and analyze complexity
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    if self._is_odoo_model(node):
                        model_name = self._get_model_name(node)
                        if model_name in self.models:
                            self._extract_methods(node, self.models[model_name])
                            
        except Exception as e:
            print(f"Error parsing model file {file_path}: {e}")
                    
    def _is_odoo_model(self, node: ast.ClassDef) -> bool:
        """Check if a class definition is an Odoo model"""
        for base in node.bases:
            if isinstance(base, ast.Attribute):
                if base.attr == 'Model':
                    return True
            elif isinstance(base, ast.Name) and base.id == 'Model':
                return True
        return False
    
    def _get_model_name(self, node: ast.ClassDef) -> Optional[str]:
        """Extract model name from a class definition"""
        for item in node.body:
            if isinstance(item, ast.Assign):
                if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                    target_name = item.targets[0].id
                    if target_name == '_name':
                        try:
                            return ast.literal_eval(item.value)
                        except (ValueError, SyntaxError):
                            pass
        return None
    
    def _extract_model_info(self, node: ast.ClassDef) -> OdooModel:
        """Extract model information from a class definition"""
        model = OdooModel(name="")
        
        for item in node.body:
            try:
                if isinstance(item, ast.Assign):
                    if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                        target_name = item.targets[0].id
                        try:
                            if target_name == '_name':
                                model.name = ast.literal_eval(item.value)
                            elif target_name == '_inherit':
                                value = ast.literal_eval(item.value)
                                model.inherit = [value] if isinstance(value, str) else value
                            elif target_name == '_description':
                                model.description = ast.literal_eval(item.value)
                            elif target_name == '_order':
                                model.order = ast.literal_eval(item.value)
                            elif target_name == '_rec_name':
                                model.record_name = ast.literal_eval(item.value)
                        except (ValueError, SyntaxError):
                            # Skip if we can't evaluate the value
                            pass
                            
                # Check for constraints
                elif isinstance(item, ast.Assign):
                    if len(item.targets) == 1 and isinstance(item.targets[0], ast.Name):
                        target_name = item.targets[0].id
                        if target_name == '_sql_constraints':
                            try:
                                constraints = ast.literal_eval(item.value)
                                model.constraints = [constraint[0] for constraint in constraints]
                            except (ValueError, SyntaxError):
                                pass
                            
                # Check for field definitions
                field = self._extract_field_info(item)
                if field:
                    model.fields[field.name] = field
                    
            except Exception as e:
                print(f"Error extracting model info: {e}")
                
        return model
    
    def _extract_methods(self, node: ast.ClassDef, model: OdooModel):
        """Extract and analyze methods in a model"""
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name
                
                # Skip private methods
                if method_name.startswith('_') and method_name not in ['_compute_', '_inverse_', '_search_']:
                    continue
                    
                method = OdooMethod(name=method_name)
                
                # Extract decorators
                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                        if decorator.func.value.id == 'api':
                            method.decorators.append(f"@api.{decorator.func.attr}")
                            
                            # Check for api.depends
                            if decorator.func.attr == 'depends':
                                method.is_compute = True
                                try:
                                    for arg in decorator.args:
                                        if isinstance(arg, ast.Str):
                                            method.api_depends.append(arg.s)
                                except:
                                    pass
                            
                            # Check for api.constrains
                            elif decorator.func.attr == 'constrains':
                                method.is_constraint = True
                                
                            # Check for api.onchange
                            elif decorator.func.attr == 'onchange':
                                method.is_onchange = True
                                
                # Extract parameters
                method.parameters = [arg.arg for arg in item.args.args if arg.arg != 'self']
                
                # Extract docstring
                if ast.get_docstring(item):
                    method.docstring = ast.get_docstring(item)
                    
                # Analyze complexity
                method.complexity = self._compute_cyclomatic_complexity(item)
                method.line_count = item.end_lineno - item.lineno
                
                model.methods[method_name] = method
                
    def _compute_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity of a function"""
        complexity = 1  # Base complexity
        
        for sub_node in ast.walk(node):
            # Add complexity for control flow statements
            if isinstance(sub_node, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(sub_node, ast.BoolOp) and isinstance(sub_node.op, (ast.And, ast.Or)):
                complexity += len(sub_node.values) - 1
                
        return complexity
    
    def _extract_field_info(self, node: ast.AST) -> Optional[OdooField]:
        """Extract field information from an assignment node"""
        try:
            # Handle standard field assignments (name = fields.Char())
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if not isinstance(target, ast.Name):
                    return None
                    
                if not isinstance(node.value, ast.Call):
                    return None
                    
                field_name = target.id
                
                # Skip private attributes and methods
                if field_name.startswith('_'):
                    return None
                
                # Get field type from fields.X() call
                if isinstance(node.value.func, ast.Attribute):
                    if hasattr(node.value.func, 'value') and hasattr(node.value.func.value, 'id'):
                        if node.value.func.value.id == 'fields':
                            field_type = node.value.func.attr
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
                    
                # Extract field parameters
                params = {}
                for kw in node.value.keywords:
                    try:
                        params[kw.arg] = ast.literal_eval(kw.value)
                    except (ValueError, SyntaxError):
                        params[kw.arg] = None
                        
                # Check for related model in relational fields
                related_model = None
                if field_type in ['Many2one', 'One2many', 'Many2many']:
                    if len(node.value.args) > 0:
                        try:
                            related_model = ast.literal_eval(node.value.args[0])
                        except (ValueError, SyntaxError):
                            pass
                            
                return OdooField(
                    name=field_name,
                    field_type=field_type,
                    related_model=related_model,
                    required=params.get('required', False),
                    string=params.get('string'),
                    default=params.get('default'),
                    compute=params.get('compute'),
                    inverse=params.get('inverse'),
                    store=params.get('store', True),
                    readonly=params.get('readonly', False),
                    index=params.get('index', False),
                    tracking=params.get('tracking', False),
                    help=params.get('help')
                )
        except Exception as e:
            print(f"Error extracting field info: {e}")
            
        return None
    
    def _parse_views(self):
        """Parse XML view files"""
        views_dir = self.module_path / 'views'
        if views_dir.exists():
            print(f"Scanning views directory: {views_dir}")
            for file_path in views_dir.glob('*.xml'):
                print(f"Processing view file: {file_path}")
                self._parse_view_file(file_path)
                
    def _parse_view_file(self, file_path: Path):
        """Parse a single view file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Simple approach: look for record tags with model="ir.ui.view"
            root = ET.fromstring(f"<root>{content}</root>")
            
            # Find all record elements
            for record in root.findall(".//record"):
                model_attr = record.get('model')
                if model_attr == 'ir.ui.view':
                    id_attr = record.get('id')
                    if id_attr:
                        # Extract fields
                        model = None
                        view_type = None
                        arch = None
                        inherit_id = None
                        priority = 16
                        field_names = []
                        
                        for field in record.findall(".//field"):
                            name_attr = field.get('name')
                            if name_attr == 'model':
                                model = field.text
                            elif name_attr == 'type':
                                view_type = field.text
                            elif name_attr == 'arch':
                                arch = ET.tostring(field, encoding='unicode')
                                # Extract field names from the arch
                                field_names = self._extract_field_names_from_arch(field)
                            elif name_attr == 'inherit_id':
                                inherit_id = field.get('ref')
                            elif name_attr == 'priority':
                                try:
                                    priority = int(field.text)
                                except (ValueError, TypeError):
                                    pass
                                    
                        if model and view_type and arch:
                            view = OdooView(
                                name=id_attr,
                                model=model,
                                type=view_type,
                                arch=arch,
                                inherit_id=inherit_id,
                                priority=priority,
                                field_names=field_names
                            )
                            self.views[id_attr] = view
                            
        except Exception as e:
            print(f"Error parsing view file {file_path}: {e}")
            
    def _extract_field_names_from_arch(self, arch_node) -> List[str]:
        """Extract field names from view architecture"""
        field_names = []
        
        try:
            # Find all field nodes
            for field in arch_node.findall(".//field"):
                name = field.get('name')
                if name:
                    field_names.append(name)
        except Exception as e:
            print(f"Error extracting field names: {e}")
            
        return field_names
            
    def _parse_security(self):
        """Parse security files and extract access rules"""
        security_dir = self.module_path / 'security'
        if security_dir.exists():
            # Parse ir.model.access.csv
            access_file = security_dir / 'ir.model.access.csv'
            if access_file.exists():
                self._parse_access_file(access_file)
                
            # Parse ir_rule_*.xml files
            for file_path in security_dir.glob('*.xml'):
                if 'rule' in file_path.name:
                    self._parse_rule_file(file_path)
                    
    def _parse_access_file(self, file_path: Path):
        """Parse ir.model.access.csv file"""
        try:
            with open(file_path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    rule = SecurityRule(
                        name=row.get('id', ''),
                        model_id=row.get('model_id:id', '').replace('model_', ''),
                        groups=[row.get('group_id:id', '')],
                        perm_read=row.get('perm_read', '0') == '1',
                        perm_write=row.get('perm_write', '0') == '1',
                        perm_create=row.get('perm_create', '0') == '1',
                        perm_unlink=row.get('perm_unlink', '0') == '1'
                    )
                    self.security_rules[rule.name] = rule
        except Exception as e:
            print(f"Error parsing access file {file_path}: {e}")
            
    def _parse_rule_file(self, file_path: Path):
        """Parse ir.rule XML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            root = ET.fromstring(f"<root>{content}</root>")
            
            # Find all record elements with model="ir.rule"
            for record in root.findall(".//record[@model='ir.rule']"):
                id_attr = record.get('id', '')
                
                model_id = None
                domain_force = None
                groups = []
                
                for field in record.findall(".//field"):
                    name_attr = field.get('name')
                    if name_attr == 'model_id':
                        ref = field.get('ref')
                        if ref:
                            model_id = ref.replace('model_', '')
                    elif name_attr == 'domain_force':
                        domain_force = field.text
                    elif name_attr == 'groups':
                        for group in field.findall(".//field"):
                            ref = group.get('ref')
                            if ref:
                                groups.append(ref)
                                
                if model_id:
                    rule = SecurityRule(
                        name=id_attr,
                        model_id=model_id,
                        groups=groups,
                        domain_force=domain_force,
                        perm_read=True,  # Assuming all permissions for rules
                        perm_write=True,
                        perm_create=True,
                        perm_unlink=True
                    )
                    self.security_rules[id_attr] = rule
                    
        except Exception as e:
            print(f"Error parsing rule file {file_path}: {e}")
            
    def _parse_menus(self):
        """Parse menu items from XML files"""
        views_dir = self.module_path / 'views'
        if views_dir.exists():
            for file_path in views_dir.glob('*.xml'):
                self._parse_menu_file(file_path)
                
    def _parse_menu_file(self, file_path: Path):
        """Parse menu items from a single XML file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            root = ET.fromstring(f"<root>{content}</root>")
            
            # Find all menuitem elements
            for menuitem in root.findall(".//menuitem"):
                id_attr = menuitem.get('id', '')
                name = menuitem.get('name', '')
                parent = menuitem.get('parent', None)
                action = menuitem.get('action', None)
                sequence = 10
                
                try:
                    sequence = int(menuitem.get('sequence', '10'))
                except ValueError:
                    pass
                    
                groups = []
                groups_attr = menuitem.get('groups', '')
                if groups_attr:
                    groups = groups_attr.split(',')
                    
                menu = OdooMenuItem(
                    id=id_attr,
                    name=name,
                    parent_id=parent,
                    action=action,
                    sequence=sequence,
                    groups=groups
                )
                self.menu_items[id_attr] = menu
                
        except Exception as e:
            print(f"Error parsing menu file {file_path}: {e}")
            
    def _analyze_dependencies(self):
        """Analyze model dependencies based on field relationships"""
        for model_name, model in self.models.items():
            self.model_dependencies[model_name] = set()
            self.field_dependencies[model_name] = set()
            
            # Add inherited models as dependencies
            for inherit in model.inherit:
                self.model_dependencies[model_name].add(inherit)
                
            # Add relational field dependencies
            for field_name, field in model.fields.items():
                if field.related_model:
                    self.model_dependencies[model_name].add(field.related_model)
                    self.field_dependencies[model_name].add((field_name, field.related_model))
                    
            # Add compute dependencies
            for method_name, method in model.methods.items():
                if method.is_compute and method.api_depends:
                    for dependency in method.api_depends:
                        parts = dependency.split('.')
                        if len(parts) > 1:
                            # This is a relation path like 'partner_id.country_id'
                            related_model = None
                            current_model = model_name
                            
                            for i, part in enumerate(parts[:-1]):
                                if part in self.models.get(current_model, OdooModel(name="")).fields:
                                    field = self.models[current_model].fields[part]
                                    if field.related_model:
                                        related_model = field.related_model
                                        current_model = related_model
                                        
                                        # Add this dependency
                                        if i == 0:  # Only add direct dependencies
                                            self.field_dependencies[model_name].add((method_name, related_model))