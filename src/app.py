import streamlit as st
import os
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
import json
import time
from src.parser import OdooModuleParser
from src.visualizer import OdooModuleVisualizer

def display_model_info(model):
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("### Model Details")
        st.write(f"**Name:** {model.name}")
        st.write(f"**Description:** {model.description}")
        
        if model.inherit:
            st.write("**Inherits from:**")
            for inherit in model.inherit:
                st.write(f"- {inherit}")
                
        if model.order:
            st.write(f"**Order:** {model.order}")
            
        if model.record_name:
            st.write(f"**Record Name Field:** {model.record_name}")
    
    with col2:
        # Info cards
        st.metric("Fields", len(model.fields) if model.fields else 0)
        st.metric("Methods", len(model.methods) if model.methods else 0)
        if model.constraints:
            st.metric("Constraints", len(model.constraints))
    
    st.divider()
    
    # Field info
    field_count = len(model.fields) if model.fields else 0
    st.write(f"### Fields ({field_count})")
    
    if model.fields:
        # Categorize fields
        basic_fields = [f for name, f in model.fields.items() 
                        if not f.compute and f.field_type not in ['Many2one', 'One2many', 'Many2many']]
        relation_fields = [f for name, f in model.fields.items() 
                          if f.field_type in ['Many2one', 'One2many', 'Many2many']]
        computed_fields = [f for name, f in model.fields.items() if f.compute]
        
        # Create tabs for different field types
        tabs = st.tabs(["All Fields", "Basic", "Relational", "Computed"])
        
        with tabs[0]:  # All Fields
            fields_data = []
            for name, field in model.fields.items():
                fields_data.append({
                    "Name": name,
                    "Type": field.field_type,
                    "Required": field.required,
                    "Related Model": field.related_model or "",
                    "Compute": field.compute or "",
                    "Readonly": field.readonly,
                    "Store": field.store,
                    "Tracking": field.tracking,
                    "Index": field.index,
                    "Help": field.help or "",
                    "Default": field.default if hasattr(field, 'default') else "",
                    "String": field.string if hasattr(field, 'string') else ""
                })
            if fields_data:
                st.dataframe(pd.DataFrame(fields_data), use_container_width=True)
        
        with tabs[1]:  # Basic
            if basic_fields:
                basic_data = []
                for field in basic_fields:
                    basic_data.append({
                        "Name": field.name,
                        "Type": field.field_type,
                        "Required": field.required,
                        "Readonly": field.readonly,
                        "Help": field.help or ""
                    })
                st.dataframe(pd.DataFrame(basic_data), use_container_width=True)
            else:
                st.info("No basic fields found")
        
        with tabs[2]:  # Relational
            if relation_fields:
                relation_data = []
                for field in relation_fields:
                    relation_data.append({
                        "Name": field.name,
                        "Type": field.field_type,
                        "Related Model": field.related_model or "",
                        "Required": field.required
                    })
                st.dataframe(pd.DataFrame(relation_data), use_container_width=True)
            else:
                st.info("No relational fields found")
        
        with tabs[3]:  # Computed
            if computed_fields:
                computed_data = []
                for field in computed_fields:
                    computed_data.append({
                        "Name": field.name,
                        "Type": field.field_type,
                        "Compute": field.compute,
                        "Stored": field.store,
                        "Readonly": field.readonly
                    })
                st.dataframe(pd.DataFrame(computed_data), use_container_width=True)
            else:
                st.info("No computed fields found")
    else:
        st.info("No fields defined")
    
    # Methods
    if model.methods:
        st.write(f"### Methods ({len(model.methods)})")
        
        # Create method data for table
        method_data = []
        for name, method in model.methods.items():
            method_data.append({
                "Name": name,
                "Type": ", ".join([d.replace("@api.", "") for d in method.decorators]) or "Regular",
                "Parameters": ", ".join(method.parameters),
                "Complexity": method.complexity,
                "Lines": method.line_count
            })
            
        if method_data:
            st.dataframe(pd.DataFrame(method_data), use_container_width=True)
        
        # Show method details with a checkbox instead of an expander
        show_method_details = st.checkbox("Show Method Details")
        if show_method_details:
            st.write("**Method Details:**")
            for name, method in model.methods.items():
                st.write(f"**{name}**")
                
                if method.decorators:
                    st.write(f"*Decorators:* {', '.join(method.decorators)}")
                    
                if method.api_depends:
                    st.write(f"*Depends on:* {', '.join(method.api_depends)}")
                    
                if method.docstring:
                    st.code(method.docstring, language="text")
                    
                st.write(f"Complexity: {method.complexity}, Lines: {method.line_count}")
                st.divider()

def display_view_info(view):
    st.write("### View Details")
    st.write(f"**Name:** {view.name}")
    st.write(f"**Model:** {view.model}")
    st.write(f"**Type:** {view.type}")
    st.write(f"**Priority:** {view.priority}")
    
    if view.inherit_id:
        st.write(f"**Inherits View:** {view.inherit_id}")
    
    if view.field_names:
        with st.expander("Fields Used"):
            for field in view.field_names:
                st.write(f"- {field}")
    
    with st.expander("View Architecture"):
        st.code(view.arch, language="xml")

def display_security_info(rules):
    st.write("### Security Rules")
    
    if not rules:
        st.info("No security rules defined in this module")
        return
    
    # Tab view for different representations
    tabs = st.tabs(["User-Friendly View", "Technical View", "Visual Permissions"])
    
    with tabs[0]:  # User-Friendly View
        st.write("This view shows security rules in plain language")
        
        for name, rule in rules.items():
            with st.expander(f"{rule.model_id} - {name}"):
                # Header with model info
                st.write(f"**Model:** {rule.model_id}")
                
                # Groups that this rule applies to
                if rule.groups:
                    st.write("**Applies to user groups:**")
                    for group in rule.groups:
                        st.write(f"- {group}")
                else:
                    st.write("**Applies to:** All users")
                
                # Permissions in user-friendly language
                st.write("**Permissions:**")
                permissions = []
                
                if rule.perm_read:
                    permissions.append("✅ **Can view** records")
                else:
                    permissions.append("❌ **Cannot view** records")
                    
                if rule.perm_write:
                    permissions.append("✅ **Can modify** existing records")
                else:
                    permissions.append("❌ **Cannot modify** existing records")
                    
                if rule.perm_create:
                    permissions.append("✅ **Can create** new records")
                else:
                    permissions.append("❌ **Cannot create** new records")
                    
                if rule.perm_unlink:
                    permissions.append("✅ **Can delete** records")
                else:
                    permissions.append("❌ **Cannot delete** records")
                
                # Display permissions
                for perm in permissions:
                    st.write(perm)
                
                # Domain explanation if exists
                if hasattr(rule, 'domain_force') and rule.domain_force:
                    st.write("**Restrictions:**")
                    st.write(f"Records must satisfy: `{rule.domain_force}`")
                    
                    # Try to provide a human-readable explanation
                    domain = rule.domain_force
                    if "'|'" in domain or "'&'" in domain:
                        st.write("*This rule contains complex conditions*")
                    else:
                        # Simple domain explanation attempts
                        if "user.id" in domain:
                            st.write("*This rule restricts access to the user's own records*")
                        if "company_id" in domain:
                            st.write("*This rule restricts access by company*")
    
    with tabs[1]:  # Technical View
        # Original technical table view
        rules_data = []
        for name, rule in rules.items():
            rules_data.append({
                "Name": name,
                "Model": rule.model_id,
                "Groups": ", ".join(rule.groups),
                "Read": rule.perm_read,
                "Write": rule.perm_write,
                "Create": rule.perm_create,
                "Unlink": rule.perm_unlink,
                "Domain": rule.domain_force if hasattr(rule, 'domain_force') else ""
            })
        st.dataframe(pd.DataFrame(rules_data))
    
    with tabs[2]:  # Visual Permissions
        # Create a visual representation of permissions
        st.write("Visual overview of who can do what with which model")
        
        # Get all unique models and groups
        all_models = sorted(set(rule.model_id for rule in rules.values()))
        all_groups = sorted(set(group for rule in rules.values() for group in rule.groups))
        
        if not all_groups:
            all_groups = ["All Users"]
        
        # Create data for heatmap
        heatmap_data = []
        
        for model in all_models:
            model_rules = [r for r in rules.values() if r.model_id == model]
            
            for group in all_groups:
                # Find rules that apply to this group and model
                applicable_rules = [r for r in model_rules if not r.groups or group in r.groups]
                
                if applicable_rules:
                    # Combine permissions from all applicable rules
                    can_read = any(r.perm_read for r in applicable_rules)
                    can_write = any(r.perm_write for r in applicable_rules)
                    can_create = any(r.perm_create for r in applicable_rules)
                    can_delete = any(r.perm_unlink for r in applicable_rules)
                    
                    # Create permission level (0-4)
                    permission_level = sum([can_read, can_write, can_create, can_delete])
                    
                    # Create permission text
                    perms = []
                    if can_read: perms.append("read")
                    if can_write: perms.append("write")
                    if can_create: perms.append("create")
                    if can_delete: perms.append("delete")
                    
                    heatmap_data.append({
                        "Model": model,
                        "Group": group,
                        "Permission Level": permission_level,
                        "Permissions": ", ".join(perms)
                    })
        
        if heatmap_data:
            df = pd.DataFrame(heatmap_data)
            
            # Create heatmap with Plotly
            fig = go.Figure(data=go.Heatmap(
                z=df['Permission Level'],
                x=df['Group'],
                y=df['Model'],
                colorscale=[
                    [0, 'rgb(255,255,255)'],  # No permissions (white)
                    [0.25, 'rgb(255,224,204)'],  # 1 permission (light orange)
                    [0.5, 'rgb(255,177,124)'],   # 2 permissions (medium orange)
                    [0.75, 'rgb(237,115,93)'],   # 3 permissions (dark orange)
                    [1, 'rgb(191,0,77)']         # 4 permissions (red)
                ],
                hoverongaps=False,
                colorbar=dict(
                    title="Permissions",
                    tickvals=[0, 1, 2, 3, 4],
                    ticktext=["None", "1 right", "2 rights", "3 rights", "Full Access"]
                ),
                hovertemplate='Model: %{y}<br>Group: %{x}<br>Permissions: %{text}<extra></extra>',
                text=df['Permissions']
            ))
            
            fig.update_layout(
                title="Access Rights by Group and Model",
                xaxis_title="User Groups",
                yaxis_title="Models",
                height=max(400, 100 + len(all_models) * 30),
                margin=dict(l=10, r=10, t=50, b=50)
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough data to create visualization")

def display_relationship_graph(nodes, edges):
    st.write("### Model Relationship Graph")
    st.write("This graph shows the relationships between models in the module.")
    
    # Debug info
    st.write(f"Nodes: {len(nodes)}, Edges: {len(edges)}")
    
    # Check if we have nodes and edges to display
    if not nodes or not edges:
        st.info("No relationships to display")
        return
    
    try:
        # Create a networkx graph
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node['id'], 
                      label=node['label'], 
                      fields=node.get('fields', 0),
                      methods=node.get('methods', 0))
        
        # Add edges
        for edge in edges:
            G.add_edge(edge['from'], edge['to'], 
                      type=edge.get('type', ''),
                      label=edge.get('label', ''),
                      field=edge.get('field', ''))
        
        # Debug info
        st.write(f"NetworkX Graph: {len(G.nodes())} nodes, {len(G.edges())} edges")
        
        # Create an interactive visualization using Pyvis
        from pyvis.network import Network
        
        # Create a pyvis network with better styling
        net = Network(height="700px", width="100%", directed=True, notebook=False, bgcolor="#ffffff", font_color="#343434")
        
        # Set physics options for better visualization
        physics_options = {
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -100,
                "centralGravity": 0.05,
                "springLength": 150,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 1
            },
            "stabilization": {
                "enabled": True,
                "iterations": 1000
            }
        }
        
        # Additional options for better appearance
        options = {
            "physics": physics_options,
            "interaction": {
                "hover": True,
                "navigationButtons": True,
                "keyboard": True,
                "multiselect": True
            },
            "edges": {
                "smooth": {
                    "enabled": True,
                    "type": "dynamic",
                    "roundness": 0.5
                },
                "font": {
                    "size": 12,
                    "strokeWidth": 0,
                    "align": "middle"
                }
            },
            "nodes": {
                "shape": "dot",
                "font": {
                    "size": 12,
                    "face": "Tahoma"
                },
                "borderWidth": 2,
                "shadow": True
            }
        }
        
        # Apply network options
        net.set_options(json.dumps(options))
        
        # Add nodes with enhanced styling
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            label = node_id.split('.')[-1] if '.' in node_id else node_id  # Display shorter names
            
            # Field and method counts
            field_count = node_data.get('fields', 0)
            method_count = node_data.get('methods', 0)
            
            # Create tooltip with additional info
            title = f"<div style='padding:10px; background:#f7f7f7; border-radius:5px;'>"
            title += f"<b style='font-size:14px;'>{node_id}</b><hr style='margin:5px 0;'>"
            title += f"Fields: {field_count}<br>Methods: {method_count}</div>"
            
            # Calculate node size based on fields and methods
            size = 15 + (field_count + method_count) * 1.5
            size = min(50, max(25, size))  # Constrain size
            
            # Color based on node type
            if "." in node_id:  # Odoo models typically have dot notation
                color = "#6929c4"  # Purple for regular models
                if node_data.get('fields', 0) > 10:
                    color = "#1192e8"  # Blue for models with many fields
            else:
                color = "#fa4d56"  # Red for non-standard models
                
            # Add node with properties
            net.add_node(node_id, 
                        label=label, 
                        title=title, 
                        size=size, 
                        color=color,
                        borderWidth=2,
                        shadow=True)
        
        # Define colors for different edge types
        edge_colors = {
            'inherits': '#525252',  # gray
            'Many2one': '#1192e8',  # blue 
            'One2many': '#ff832b',  # orange
            'Many2many': '#a56eff',  # purple
            'default': '#878787'     # light gray
        }
        
        # Add edges with relationship type colors and tooltips
        for source, target, data in G.edges(data=True):
            edge_type = data.get('type', 'default')
            field = data.get('field', '')
            
            # Create styled edge tooltip
            edge_tooltip = f"<div style='padding:8px; background:#f7f7f7; border-radius:5px;'>"
            edge_tooltip += f"<b>Type:</b> {edge_type}<br>"
            if field:
                edge_tooltip += f"<b>Field:</b> {field}"
            edge_tooltip += "</div>"
            
            # Choose color based on edge type
            color = edge_colors.get(edge_type, edge_colors['default'])
            
            # Add edge to network with appropriate styling
            net.add_edge(source, target, 
                        title=edge_tooltip, 
                        color=color, 
                        label=field if field else "", 
                        arrows='to' if edge_type != 'inherits' else 'from',
                        dashes=(edge_type != 'Many2one'),
                        smooth=True,
                        width=2 if edge_type == 'Many2one' else 1)
        
        # Generate temporary HTML file with a unique name to avoid caching issues
        html_path = f"temp_network_{int(time.time())}.html"
        net.save_graph(html_path)
        
        # Read the HTML file and apply custom CSS fixes for Streamlit
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Add custom CSS for better appearance in Streamlit
        custom_css = """
        <style>
        .vis-network {
            border: 1px solid #ddd;
            border-radius: 5px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        </style>
        """
        
        # Insert custom CSS into HTML
        html_content = html_content.replace('</head>', custom_css + '</head>')
        
        # Re-save modified HTML
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        # Re-read the file for display
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Display in Streamlit
        st.components.v1.html(html_content, height=700, scrolling=False)
        
        # Clean up
        if os.path.exists(html_path):
            os.remove(html_path)
        
        # Show model dependencies as a table for reference
        with st.expander("Model Dependencies (Table View)"):
            deps = []
            for source, target in G.edges():
                deps.append({"Source": source, "Target": target})
            if deps:
                st.table(pd.DataFrame(deps))
            else:
                st.write("No dependencies found")
                
    except Exception as e:
        st.error(f"Error displaying relationship graph: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def display_code_quality(metrics):
    st.write("### Code Quality Analysis")
    
    # Create columns for different metric types
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### Missing Descriptions")
        if metrics['missing_descriptions']:
            for item in metrics['missing_descriptions']:
                st.warning(item)
        else:
            st.success("All models have descriptions!")
            
        st.write("#### Performance Concerns")
        if metrics['performance_concerns']:
            for item in metrics['performance_concerns']:
                st.warning(item)
        else:
            st.success("No performance concerns found!")
    
    with col2:
        st.write("#### Security Issues")
        if metrics['security_issues']:
            for item in metrics['security_issues']:
                st.error(item)
        else:
            st.success("No security issues found!")
            
        st.write("#### Unused Fields")
        if metrics['unused_fields']:
            for item in metrics['unused_fields']:
                st.info(item)
        else:
            st.success("No potentially unused fields found!")

def display_module_stats(stats):
    st.write("### Module Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Models", stats['total_models'])
        st.metric("Fields", stats['total_fields'])
        st.metric("Methods", stats['total_methods'])
        
    with col2:
        st.metric("Inheriting Models", stats['inheritance']['models_inheriting'])
        st.metric("Security Coverage", f"{stats['security_coverage']['coverage_percentage']}%")
        
    with col3:
        view_count = sum(stats['views_by_type'].values()) if 'views_by_type' in stats else 0
        st.metric("Views", view_count)
        
    # Field types distribution
    if stats.get('field_types'):
        st.subheader("Field Type Distribution")
        field_df = pd.DataFrame({
            'Type': list(stats['field_types'].keys()),
            'Count': list(stats['field_types'].values())
        })
        field_df = field_df.sort_values('Count', ascending=False)
        
        fig = go.Figure(data=[
            go.Bar(
                x=field_df['Type'],
                y=field_df['Count'],
                marker_color='rgb(55, 83, 109)'
            )
        ])
        fig.update_layout(
            margin=dict(l=40, r=40, t=40, b=40),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)
        
    # Model size comparison
    if stats.get('model_size'):
        st.subheader("Model Size Comparison")
        
        model_sizes = []
        for model, size in stats['model_size'].items():
            model_sizes.append({
                'Model': model,
                'Fields': size['fields'],
                'Methods': size['methods'],
                'Total': size['fields'] + size['methods']
            })
            
        model_df = pd.DataFrame(model_sizes).sort_values('Total', ascending=False)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=model_df['Model'],
            y=model_df['Fields'],
            name='Fields',
            marker_color='rgb(55, 126, 184)'
        ))
        fig.add_trace(go.Bar(
            x=model_df['Model'],
            y=model_df['Methods'],
            name='Methods',
            marker_color='rgb(255, 127, 0)'
        ))
        
        fig.update_layout(
            barmode='stack',
            margin=dict(l=40, r=40, t=40, b=60),
            height=400,
            xaxis_tickangle=-45
        )
        
        st.plotly_chart(fig, use_container_width=True)

def disable_hover_effects(html_content):
    """
    Modifies the HTML content to disable hover effects in the visualization
    """
    # Add CSS to disable hover effects
    hover_disable_css = """
    <style>
    .node:hover, .link:hover {
      cursor: default !important;
    }
    
    .tooltip {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
    }
    </style>
    """
    
    # Insert the CSS before the closing </head> tag
    if "</head>" in html_content:
        modified_html = html_content.replace("</head>", hover_disable_css + "</head>")
        return modified_html
    else:
        # If no head tag, just append it at the beginning
        return hover_disable_css + html_content

def main():
    st.set_page_config(
        page_title="Odoo Module Visualizer",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("Odoo Module Analyzer")
    
    # Module path input
    module_path = st.text_input(
        "Enter the path to your Odoo module:",
        value="",
        help="Provide the absolute path to your Odoo module directory"
    )
    
    if not module_path:
        st.warning("Please enter a module path to begin analysis")
        return
        
    if not os.path.exists(module_path):
        st.error("The specified path does not exist")
        return
        
    try:
        # Parse module with progress indication
        progress_text = "Analyzing module..."
        my_bar = st.progress(0, text=progress_text)
        
        # Start time measurement
        start_time = time.time()
        
        # Parse module
        parser = OdooModuleParser(module_path)
        my_bar.progress(25, text="Parsing module structure...")
        parser.parse_module()
        my_bar.progress(50, text="Generating visualizations...")
        
        # Create visualizer
        visualizer = OdooModuleVisualizer(parser)
        my_bar.progress(75, text="Analyzing code quality...")
        
        # Get metrics
        code_metrics = visualizer.analyze_code_quality()
        module_stats = visualizer.get_module_stats()
        
        # Generate relationship graph
        nodes, edges = visualizer.generate_relationship_graph()
        
        my_bar.progress(100, text="Analysis complete!")
        
        # Calculate and display analysis time
        analysis_time = time.time() - start_time
        st.write(f"**Analysis completed in {analysis_time:.2f} seconds**")
        
        # Create tabs for different views
        tab_tree, tab_models, tab_relationships, tab_quality, tab_stats, tab_export = st.tabs([
            "Tree Visualization",
            "Models",
            "Relationships",
            "Code Quality",
            "Statistics",
            "Export"
        ])
        
        # Visualization tab
        with tab_tree:
            st.write("## Module Tree Structure")
            
            # Show module stats
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Models", len(parser.models))
            with col2:
                st.metric("Fields", sum(len(model.fields) for model in parser.models.values()))
            with col3:
                st.metric("Security Rules", len(parser.security_rules))
            
            # Generate visualization
            html_path = "temp_tree.html"
            visualizer.generate_html(html_path)
            
            with open(html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Disable hover effects in the HTML
            modified_html = disable_hover_effects(html_content)
            
            # Display visualization with full height
            st.components.v1.html(modified_html, height=1200, scrolling=True)
            
            # Clean up
            if os.path.exists(html_path):
                os.remove(html_path)
        
        # Models tab
        with tab_models:
            st.write("## Models")
            
            if parser.models:
                # Group models by inheritance
                base_models = {name: model for name, model in parser.models.items() if not model.inherit}
                inherited_models = {name: model for name, model in parser.models.items() if model.inherit}
                
                # Create two columns
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("### Base Models")
                    base_model_names = sorted(base_models.keys())
                    if base_model_names:
                        selected_base = st.selectbox(
                            "Select a base model:",
                            options=base_model_names
                        )
                        if selected_base:
                            with st.expander("Base Model Details", expanded=True):
                                display_model_info(base_models[selected_base])
                    else:
                        st.info("No base models found")
                
                with col2:
                    st.write("### Inherited Models")
                    inherited_model_names = sorted(inherited_models.keys())
                    if inherited_model_names:
                        selected_inherited = st.selectbox(
                            "Select an inherited model:",
                            options=inherited_model_names
                        )
                        if selected_inherited:
                            with st.expander("Inherited Model Details", expanded=True):
                                display_model_info(inherited_models[selected_inherited])
                    else:
                        st.info("No inherited models found")
            else:
                st.info("No models found in this module")
                
        # Relationships tab
        with tab_relationships:
            st.write("## Model Relationships")
            display_relationship_graph(nodes, edges)
            
        # Code Quality tab
        with tab_quality:
            st.write("## Code Quality")
            display_code_quality(code_metrics)
            
        # Statistics tab  
        with tab_stats:
            st.write("## Module Statistics")
            display_module_stats(module_stats)
            
        # Export tab
        with tab_export:
            st.write("## Export Module Data")
            
            export_format = st.selectbox(
                "Select export format",
                options=["JSON", "HTML Report"]
            )
            
            if st.button("Export"):
                if export_format == "JSON":
                    # Export to JSON
                    export_path = "module_data.json"
                    visualizer.export_module_data(export_path)
                    
                    # Offer for download
                    with open(export_path, 'r') as f:
                        json_data = f.read()
                    
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"{os.path.basename(module_path)}_analysis.json",
                        mime="application/json"
                    )
                    
                    # Clean up
                    if os.path.exists(export_path):
                        os.remove(export_path)
                        
                elif export_format == "HTML Report":
                    st.info("HTML Report export coming soon!")
                
    except Exception as e:
        st.error(f"Error analyzing module: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

if __name__ == '__main__':
    main()