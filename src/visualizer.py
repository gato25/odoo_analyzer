import os
import json
from typing import Dict, List, Optional, Tuple
from src.parser import OdooModuleParser

class OdooModuleVisualizer:
    def __init__(self, parser: OdooModuleParser):
        self.parser = parser
        
    def generate_html(self, output_path: str):
        """Generate HTML visualization with tree structure"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {
                    margin: 0;
                    padding: 0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f8f9fa;
                    height: 100%;
                    overflow-y: auto;
                }
                html {
                    height: 100%;
                    overflow: hidden;
                }
                .tree {
                    margin: 0;
                    padding: 30px;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    min-height: calc(100vh - 60px); /* Full viewport height minus padding */
                    position: relative;
                }
                .tree ul {
                    padding-left: 25px;
                    list-style: none;
                }
                .tree li {
                    position: relative;
                    padding: 6px 0;
                }
                .tree li::before {
                    content: "";
                    position: absolute;
                    left: -15px;
                    top: 15px;
                    width: 10px;
                    height: 2px;
                    background: #ddd;
                }
                .tree li::after {
                    content: "";
                    position: absolute;
                    left: -15px;
                    top: 0;
                    width: 2px;
                    height: 100%;
                    background: #ddd;
                }
                .tree li:last-child::after {
                    height: 15px;
                }
                .tree li:first-child::before {
                    display: none;
                }
                .node {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 6px;
                    margin: 2px 0;
                    cursor: pointer;
                    transition: all 0.2s ease;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                }
                .node:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .model {
                    background: linear-gradient(135deg, #e3f2fd, #bbdefb);
                    border: 1px solid #90caf9;
                    color: #1565c0;
                }
                .security {
                    background: linear-gradient(135deg, #fff8e1, #ffe082);
                    border: 1px solid #ffca28;
                    color: #ff8f00;
                }
                .field {
                    background: linear-gradient(135deg, #f3e5f5, #e1bee7);
                    border: 1px solid #ce93d8;
                    color: #7b1fa2;
                    font-size: 0.9em;
                }
                .field-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 8px;
                    padding: 8px;
                    background-color: #fafafa;
                    border-radius: 8px;
                }
                .tooltip {
                    display: none;
                    position: absolute;
                    background: white;
                    border: none;
                    padding: 12px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                    z-index: 1000;
                    max-width: 300px;
                    left: 100%;
                    top: 0;
                    margin-left: 10px;
                    font-size: 0.9em;
                    line-height: 1.5;
                    color: #333;
                }
                .node:hover .tooltip {
                    display: block;
                    animation: fadeIn 0.3s;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .expandable {
                    cursor: pointer;
                }
                .expandable::before {
                    content: "▶";
                    display: inline-block;
                    margin-right: 8px;
                    transition: transform 0.3s;
                    color: #888;
                    font-size: 10px;
                }
                .expandable.expanded::before {
                    transform: rotate(90deg);
                    color: #333;
                }
                .hidden {
                    display: none;
                }
                .field-count {
                    background-color: rgba(0,0,0,0.1);
                    border-radius: 12px;
                    padding: 2px 8px;
                    font-size: 0.8em;
                    margin-left: 8px;
                    font-weight: 500;
                }
                .model-header {
                    display: flex;
                    align-items: center;
                }
                .section-title {
                    font-size: 1.2em;
                    font-weight: 600;
                    margin-left: 8px;
                }
                .tooltip-title {
                    font-weight: 600;
                    margin-bottom: 8px;
                    padding-bottom: 5px;
                    border-bottom: 1px solid #eee;
                }
                .tooltip-section {
                    margin-top: 5px;
                }
                .field-type {
                    opacity: 0.7;
                    font-size: 0.85em;
                    font-style: italic;
                }
                .header {
                    background-color: #f5f5f5;
                    padding: 15px 20px;
                    border-radius: 8px;
                    margin-bottom: 15px;
                    border-left: 4px solid #2196f3;
                }
                
                /* Navigation controls */
                .controls {
                    position: fixed;
                    bottom: 20px;
                    right: 20px;
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    z-index: 1000;
                }
                .control-btn {
                    width: 40px;
                    height: 40px;
                    background: white;
                    border: none;
                    border-radius: 50%;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    color: #555;
                    transition: all 0.2s;
                }
                .control-btn:hover {
                    background: #f0f0f0;
                    transform: scale(1.1);
                }
                .scroll-indicator {
                    position: fixed;
                    bottom: 10px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: rgba(0,0,0,0.5);
                    color: white;
                    padding: 5px 10px;
                    border-radius: 15px;
                    font-size: 12px;
                    opacity: 0;
                    transition: opacity 0.3s;
                    z-index: 1000;
                }
                .scroll-indicator.visible {
                    opacity: 1;
                }
            </style>
            <script>
                function toggleNode(element) {
                    const ul = element.nextElementSibling;
                    if (ul && ul.tagName === 'UL') {
                        element.classList.toggle('expanded');
                        ul.classList.toggle('hidden');
                    }
                }
                
                // Auto-expand all nodes on load
                window.onload = function() {
                    // Expand all model nodes by default
                    document.querySelectorAll('.expandable').forEach(node => {
                        node.click();
                    });
                    
                    // Add scroll event listener
                    window.addEventListener('scroll', function() {
                        const scrollIndicator = document.getElementById('scroll-indicator');
                        const scrollHeight = document.documentElement.scrollHeight;
                        const scrollTop = document.documentElement.scrollTop;
                        const clientHeight = document.documentElement.clientHeight;
                        
                        // Show scroll indicator when not at the bottom
                        if (scrollTop + clientHeight < scrollHeight - 50) {
                            scrollIndicator.classList.add('visible');
                        } else {
                            scrollIndicator.classList.remove('visible');
                        }
                    });
                };
                
                // Scroll functions
                function scrollToTop() {
                    window.scrollTo({top: 0, behavior: 'smooth'});
                }
                
                function scrollToBottom() {
                    window.scrollTo({top: document.documentElement.scrollHeight, behavior: 'smooth'});
                }
                
                // Expand/collapse all nodes
                function expandAll() {
                    document.querySelectorAll('.expandable:not(.expanded)').forEach(node => {
                        node.click();
                    });
                }
                
                function collapseAll() {
                    document.querySelectorAll('.expandable.expanded').forEach(node => {
                        node.click();
                    });
                }
            </script>
        </head>
        <body>
            <div class="tree">
                <div class="header">
                    <h2 style="margin:0">Odoo Module Structure</h2>
                    <p style="margin:5px 0 0 0; color:#666;">Interactive visualization of models and security rules</p>
                </div>
                <ul>
        """
        
        # Add models
        html_content += self._generate_model_tree()
        
        # Add security rules
        html_content += self._generate_security_tree()
        
        html_content += """
                </ul>
            </div>
            
            <!-- Navigation controls -->
            <div class="controls">
                <button class="control-btn" onclick="scrollToTop()" title="Scroll to top">↑</button>
                <button class="control-btn" onclick="expandAll()" title="Expand all">+</button>
                <button class="control-btn" onclick="collapseAll()" title="Collapse all">-</button>
                <button class="control-btn" onclick="scrollToBottom()" title="Scroll to bottom">↓</button>
            </div>
            
            <!-- Scroll indicator -->
            <div id="scroll-indicator" class="scroll-indicator">Scroll down for more content</div>
        </body>
        </html>
        """
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
    def _generate_model_tree(self) -> str:
        """Generate HTML for model tree structure"""
        html = '<li><div class="node model expandable expanded" onclick="toggleNode(this)"><span class="section-title">📦 Models</span></div><ul>'
        
        # Add base models first
        base_models = []
        for model_name, model in self.parser.models.items():
            if not model.inherit:
                base_models.append((model_name, model))
                
        # Add inherited models
        inherited_models = []
        for model_name, model in self.parser.models.items():
            if model.inherit:
                inherited_models.append((model_name, model))
                
        # Sort models by name
        base_models.sort(key=lambda x: x[0])
        inherited_models.sort(key=lambda x: x[0])
        
        # Render base models
        if base_models:
            html += '<li><div class="node model expandable expanded" onclick="toggleNode(this)">Base Models</div><ul>'
            for model_name, model in base_models:
                html += self._generate_model_node(model_name, model)
            html += '</ul></li>'
            
        # Render inherited models
        if inherited_models:
            html += '<li><div class="node model expandable expanded" onclick="toggleNode(this)">Inherited Models</div><ul>'
            for model_name, model in inherited_models:
                html += self._generate_model_node(model_name, model)
            html += '</ul></li>'
        
        html += '</ul></li>'
        return html
        
    def _generate_model_node(self, model_name: str, model) -> str:
        """Generate HTML for a single model node"""
        tooltip = f"""
            <div class="tooltip">
                <div class="tooltip-title">Model: {model_name}</div>
                <div class="tooltip-section">Description: {model.description or "None"}</div>
                <div class="tooltip-section">Fields: {len(model.fields)}</div>
                <div class="tooltip-section">Methods: {len(model.methods)}</div>
                {f'<div class="tooltip-section">Inherits: {", ".join(model.inherit)}</div>' if model.inherit else ""}
            </div>
        """
        
        field_count = len(model.fields) if model.fields else 0
        
        html = f'<li><div class="node model expandable expanded" onclick="toggleNode(this)"><div class="model-header">{model_name.split(".")[-1]} <span class="field-count">{field_count} fields</span>{tooltip}</div></div>'
        
        # Add fields
        if model.fields:
            html += '<ul>'
            
            # Get field categories
            basic_fields = []
            relational_fields = []
            computed_fields = []
            
            for field_name, field in model.fields.items():
                if field.compute:
                    computed_fields.append((field_name, field))
                elif field.field_type in ['Many2one', 'One2many', 'Many2many']:
                    relational_fields.append((field_name, field))
                else:
                    basic_fields.append((field_name, field))
            
            # Sort fields by name
            basic_fields.sort(key=lambda x: x[0])
            relational_fields.sort(key=lambda x: x[0])
            computed_fields.sort(key=lambda x: x[0])
            
            # Add basic fields
            if basic_fields:
                html += '<li><div>Basic Fields</div><div class="field-container">'
                for field_name, field in basic_fields:
                    html += self._generate_field_node(field_name, field)
                html += '</div></li>'
                
            # Add relational fields
            if relational_fields:
                html += '<li><div>Relational Fields</div><div class="field-container">'
                for field_name, field in relational_fields:
                    html += self._generate_field_node(field_name, field)
                html += '</div></li>'
                
            # Add computed fields
            if computed_fields:
                html += '<li><div>Computed Fields</div><div class="field-container">'
                for field_name, field in computed_fields:
                    html += self._generate_field_node(field_name, field)
                html += '</div></li>'
                
            html += '</ul>'
        else:
            html += '<ul><li>No fields defined</li></ul>'
            
        html += '</li>'
        return html
        
    def _generate_field_node(self, field_name: str, field) -> str:
        """Generate HTML for a field node"""
        tooltip = f"""
            <div class="tooltip">
                <div class="tooltip-title">Field: {field_name}</div>
                <div class="tooltip-section">Type: {field.field_type}</div>
                <div class="tooltip-section">Required: {field.required}</div>
                {f'<div class="tooltip-section">Related Model: {field.related_model}</div>' if field.related_model else ""}
                {f'<div class="tooltip-section">Compute: {field.compute}</div>' if field.compute else ""}
                <div class="tooltip-section">Readonly: {field.readonly}</div>
                <div class="tooltip-section">Store: {field.store}</div>
            </div>
        """
        
        return f'<div class="node field">{field_name} <span class="field-type">({field.field_type})</span>{tooltip}</div>'
        
    def _generate_security_tree(self) -> str:
        """Generate HTML for security rules tree structure"""
        if not self.parser.security_rules:
            return ""
            
        html = '<li><div class="node security expandable expanded" onclick="toggleNode(this)"><span class="section-title">🔐 Security Rules</span></div><ul>'
        
        # Group rules by model
        model_rules = {}
        for rule_name, rule in self.parser.security_rules.items():
            model_id = rule.model_id
            if model_id not in model_rules:
                model_rules[model_id] = []
            model_rules[model_id].append((rule_name, rule))
            
        # Sort models
        sorted_models = sorted(model_rules.keys())
        
        for model_id in sorted_models:
            rules = model_rules[model_id]
            html += f'<li><div class="node security expandable" onclick="toggleNode(this)">{model_id} ({len(rules)} rules)</div><ul class="hidden">'
            
            for rule_name, rule in sorted(rules, key=lambda x: x[0]):
                tooltip = f"""
                    <div class="tooltip">
                        <div class="tooltip-title">Rule: {rule_name}</div>
                        <div class="tooltip-section">Model: {rule.model_id}</div>
                        <div class="tooltip-section">Groups: {', '.join(rule.groups)}</div>
                        <div class="tooltip-section">Permissions:</div>
                        <div>Read: {rule.perm_read}</div>
                        <div>Write: {rule.perm_write}</div>
                        <div>Create: {rule.perm_create}</div>
                        <div>Unlink: {rule.perm_unlink}</div>
                    </div>
                """
                html += f'<li><div class="node security">{rule_name}{tooltip}</div></li>'
                
            html += '</ul></li>'
            
        html += '</ul></li>'
        return html

    def generate_relationship_graph(self) -> Tuple[List[dict], List[dict]]:
        """Generate nodes and edges for model relationships visualization"""
        nodes = []
        edges = []
        
        # Add model nodes
        for model_name, model in self.parser.models.items():
            nodes.append({
                'id': model_name,
                'label': model_name,
                'type': 'model',
                'fields': len(model.fields),
                'methods': len(model.methods),
                'description': model.description
            })
            
            # Add inheritance edges
            for inherit in model.inherit:
                edges.append({
                    'from': model_name,
                    'to': inherit,
                    'type': 'inherits',
                    'label': 'inherits'
                })
                
            # Add field relationship edges
            for field_name, field in model.fields.items():
                if field.related_model:
                    edges.append({
                        'from': model_name,
                        'to': field.related_model,
                        'type': field.field_type,
                        'label': field.field_type,
                        'field': field_name
                    })
        
        return nodes, edges
    
    def export_module_data(self, output_path: str):
        """Export module data to JSON for external use"""
        module_data = {
            'module_name': os.path.basename(self.parser.module_path),
            'models': {},
            'security_rules': {},
            'views': {}
        }
        
        # Export models
        for model_name, model in self.parser.models.items():
            model_data = {
                'name': model.name,
                'description': model.description,
                'inherit': model.inherit,
                'fields': {},
                'methods': model.methods
            }
            
            # Export fields
            for field_name, field in model.fields.items():
                model_data['fields'][field_name] = {
                    'type': field.field_type,
                    'required': field.required,
                    'related_model': field.related_model,
                    'compute': field.compute,
                    'store': field.store,
                    'readonly': field.readonly
                }
                
            module_data['models'][model_name] = model_data
            
        # Export security rules
        for rule_name, rule in self.parser.security_rules.items():
            module_data['security_rules'][rule_name] = {
                'model_id': rule.model_id,
                'groups': rule.groups,
                'perm_read': rule.perm_read,
                'perm_write': rule.perm_write,
                'perm_create': rule.perm_create,
                'perm_unlink': rule.perm_unlink
            }
            
        # Export views
        for view_name, view in self.parser.views.items():
            module_data['views'][view_name] = {
                'model': view.model,
                'type': view.type,
                'inherit_id': view.inherit_id,
                'priority': view.priority
            }
            
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(module_data, f, indent=2)
            
        return output_path
    
    def analyze_code_quality(self) -> Dict:
        """Analyze code quality and return metrics"""
        metrics = {
            'missing_descriptions': [],
            'complex_methods': [],
            'unused_fields': [],
            'security_issues': [],
            'performance_concerns': []
        }
        
        # Check for missing descriptions
        for model_name, model in self.parser.models.items():
            if not model.description:
                metrics['missing_descriptions'].append(f"Model {model_name} has no description")
            
            # Check for unused fields (One2many fields with no inverse Many2one)
            for field_name, field in model.fields.items():
                if field.field_type == 'One2many':
                    if field.related_model and not self._has_inverse_field(model_name, field):
                        metrics['unused_fields'].append(f"Field {model_name}.{field_name} might be unused (no inverse Many2one field found)")
                
                # Check for non-stored computed fields that might impact performance
                if field.compute and not field.store:
                    metrics['performance_concerns'].append(f"Non-stored computed field {model_name}.{field_name} might impact performance")
        
        # Check for security issues
        model_access = set()
        for rule in self.parser.security_rules.values():
            model_access.add(rule.model_id)
            
        for model_name in self.parser.models:
            if model_name not in model_access:
                metrics['security_issues'].append(f"Model {model_name} has no access rules defined")
                
        return metrics
    
    def _has_inverse_field(self, model_name: str, one2many_field) -> bool:
        """Check if a One2many field has an inverse Many2one field in the related model"""
        related_model_name = one2many_field.related_model
        if related_model_name not in self.parser.models:
            return False
            
        related_model = self.parser.models[related_model_name]
        for field in related_model.fields.values():
            if field.field_type == 'Many2one' and field.related_model == model_name:
                return True
                
        return False
    
    def get_module_stats(self) -> Dict:
        """Get comprehensive statistics about the module"""
        stats = {
            'total_models': len(self.parser.models),
            'total_fields': sum(len(model.fields) for model in self.parser.models.values()),
            'total_methods': sum(len(model.methods) for model in self.parser.models.values()),
            'field_types': {},
            'model_size': {},
            'inheritance': {
                'models_inheriting': len([m for m in self.parser.models.values() if m.inherit]),
                'inheritance_chains': self._get_inheritance_chains()
            },
            'views_by_type': {},
            'security_coverage': self._get_security_coverage()
        }
        
        # Count field types
        for model in self.parser.models.values():
            for field in model.fields.values():
                if field.field_type not in stats['field_types']:
                    stats['field_types'][field.field_type] = 0
                stats['field_types'][field.field_type] += 1
                
            # Model size metrics
            stats['model_size'][model.name] = {
                'fields': len(model.fields),
                'methods': len(model.methods)
            }
            
        # Count view types
        for view in self.parser.views.values():
            if view.type not in stats['views_by_type']:
                stats['views_by_type'][view.type] = 0
            stats['views_by_type'][view.type] += 1
            
        return stats
    
    def _get_inheritance_chains(self) -> List[List[str]]:
        """Get chains of model inheritance"""
        chains = []
        models = self.parser.models
        
        def build_chain(model_name, chain=None):
            if chain is None:
                chain = []
                
            chain.append(model_name)
            
            if model_name in models and models[model_name].inherit:
                for parent in models[model_name].inherit:
                    new_chain = chain.copy()
                    if parent in models:
                        build_chain(parent, new_chain)
                        chains.append(new_chain)
                    else:
                        new_chain.append(parent)
                        chains.append(new_chain)
            else:
                chains.append(chain)
                
        for model_name in models:
            if not any(model_name in chain for chain in chains):
                build_chain(model_name)
                
        return chains
    
    def _get_security_coverage(self) -> Dict:
        """Calculate security coverage stats"""
        total_models = len(self.parser.models)
        models_with_rules = set()
        
        for rule in self.parser.security_rules.values():
            if rule.model_id in self.parser.models:
                models_with_rules.add(rule.model_id)
                
        return {
            'models_with_rules': len(models_with_rules),
            'coverage_percentage': round(len(models_with_rules) / total_models * 100, 2) if total_models > 0 else 0,
            'models_missing_rules': list(set(self.parser.models.keys()) - models_with_rules)
        }