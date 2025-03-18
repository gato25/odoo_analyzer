# Odoo Module Analyzer

An advanced analytical tool for Odoo modules that helps you understand module structure, relationships, and code quality.

## Features

- **Interactive Tree Visualization**: Explore your Odoo module's structure with an interactive, collapsible tree view
- **Model Analysis**: View detailed information about models, fields, and their relationships
- **Field Categorization**: Fields are organized by type (basic, relational, computed) for easier understanding
- **Security Rule Overview**: Examine security rules grouped by model
- **Code Quality Metrics**: Identify potential issues like missing descriptions, security gaps, and performance concerns
- **Relationship Graphs**: Visual representation of model relationships and dependencies
- **Module Statistics**: Detailed charts and metrics about your module's composition
- **Export Functionality**: Export analysis results for further processing
- **Method Analysis**: Examine method complexity, dependencies, and documentation
- **View Field Usage**: See which fields are used in views and track field references
- **Beautiful UI**: Clean, modern interface with tooltips and detailed information panels

## Installation

1. Clone the repository or download the source code
2. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the analyzer using either:

```bash
python run.py
```

Or directly with Streamlit:

```bash
cd odoo_analyzer
streamlit run src/app.py
```

### How to Use

1. Enter the path to your Odoo module (e.g., `C:\Users\developer\KAMI\nomin\odoo-16.0\custom_addons\todo_app`)
2. Explore the visualization in the "Tree Visualization" tab
3. Examine model details in the "Models" tab
4. Analyze relationship graphs in the "Relationships" tab
5. Check code quality metrics in the "Code Quality" tab
6. View statistics and charts in the "Statistics" tab
7. Export analysis results in the "Export" tab

## Tree Visualization

The tree structure provides a hierarchical view of your Odoo module:

- **Models**: Base models and inherited models are clearly separated
- **Fields**: Fields are categorized as basic, relational, or computed
- **Security Rules**: Security rules are grouped by model

## Relationship Graphs

The relationship visualization shows how models are connected:

- **Inheritance**: See which models inherit from others
- **Relational Fields**: View Many2one, One2many, and Many2many relationships
- **Interactive**: Hover over connections for more details

## Code Quality Analysis

Identifies potential issues in your module:

- **Missing Descriptions**: Models without proper descriptions
- **Security Issues**: Models without access rules
- **Performance Concerns**: Non-stored computed fields that might impact performance
- **Unused Fields**: One2many fields without corresponding Many2one fields

## Requirements

- Python 3.8+
- Streamlit
- NetworkX
- Pandas
- Plotly
- PyVis

## Notes

- Hover over any element to see detailed tooltips
- Click on the triangle icons to expand/collapse sections
- Models are color-coded to differentiate between base models and inherited models 