"""
Tests for JavaScript/TypeScript signature extraction.
"""

import pytest
import os
import tempfile
from contextor.signatures.javascript import (
    extract_imports_exports,
    extract_functions,
    extract_classes,
    extract_react_functional_components,
    extract_typescript_interfaces,
    get_js_signatures,
    process_js_file
)

@pytest.fixture
def js_file():
    """Create a temporary JavaScript file for testing."""
    content = """
import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';

// Simple function
function fetchData(url) {
    return axios.get(url);
}

// Arrow function
const processData = (data) => {
    return data.map(item => item.value);
};

// Class
class DataProcessor {
    constructor(config) {
        this.config = config;
    }
    
    process(data) {
        return data.filter(this.config.filterFn);
    }
}

// React component class
class DataComponent extends React.Component {
    constructor(props) {
        super(props);
        this.state = { data: [] };
    }
    
    componentDidMount() {
        fetchData(this.props.url).then(response => {
            this.setState({ data: response.data });
        });
    }
    
    render() {
        return (
            <div>
                {this.state.data.map(item => (
                    <div key={item.id}>{item.name}</div>
                ))}
            </div>
        );
    }
}

// Functional component
const DataList = ({ items }) => {
    const [filtered, setFiltered] = useState(items);
    
    useEffect(() => {
        setFiltered(processData(items));
    }, [items]);
    
    return (
        <ul>
            {filtered.map(item => (
                <li key={item.id}>{item.name}</li>
            ))}
        </ul>
    );
};

export { fetchData, processData, DataProcessor };
export default DataComponent;
"""
    
    with tempfile.NamedTemporaryFile(suffix='.js', delete=False, mode='w') as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    os.unlink(temp_file)

@pytest.fixture
def ts_file():
    """Create a temporary TypeScript file for testing."""
    content = """
import React from 'react';
import { useState, useEffect } from 'react';
import axios from 'axios';

// TypeScript interfaces
interface Item {
    id: number;
    name: string;
    value: any;
}

interface DataProps {
    url: string;
    filter?: (item: Item) => boolean;
}

// Simple function
function fetchData(url: string): Promise<Item[]> {
    return axios.get(url);
}

// Arrow function
const processData = (data: Item[]): any[] => {
    return data.map(item => item.value);
};

// Class
class DataProcessor {
    private config: any;
    
    constructor(config: any) {
        this.config = config;
    }
    
    process(data: Item[]): Item[] {
        return data.filter(this.config.filterFn);
    }
}

// React component
const DataList: React.FC<{items: Item[]}> = ({ items }) => {
    const [filtered, setFiltered] = useState<Item[]>(items);
    
    useEffect(() => {
        setFiltered(processData(items) as Item[]);
    }, [items]);
    
    return (
        <ul>
            {filtered.map(item => (
                <li key={item.id}>{item.name}</li>
            ))}
        </ul>
    );
};

export { fetchData, processData, DataProcessor };
export default DataList;
"""
    
    with tempfile.NamedTemporaryFile(suffix='.ts', delete=False, mode='w') as f:
        f.write(content)
        temp_file = f.name
    
    yield temp_file
    os.unlink(temp_file)

def test_extract_imports_exports(js_file):
    """Test extraction of import and export statements."""
    with open(js_file, 'r') as f:
        content = f.read()
    
    result = extract_imports_exports(content)
    
    assert len(result["imports"]) >= 3
    assert "import React from 'react';" in result["imports"]
    
    assert len(result["exports"]) >= 2
    assert any("export { fetchData" in exp for exp in result["exports"])
    assert any("export default" in exp for exp in result["exports"])

def test_extract_functions(js_file):
    """Test extraction of function declarations."""
    with open(js_file, 'r') as f:
        content = f.read()
    
    functions = extract_functions(content)
    
    assert len(functions) >= 2
    function_names = [f["name"] for f in functions]
    assert "fetchData" in function_names
    assert "processData" in function_names

def test_extract_classes(js_file):
    """Test extraction of class declarations."""
    with open(js_file, 'r') as f:
        content = f.read()
    
    classes = extract_classes(content)
    
    assert len(classes) >= 2
    class_names = [c["name"] for c in classes]
    assert "DataProcessor" in class_names
    assert "DataComponent" in class_names
    
    # Test React component detection
    for cls in classes:
        if cls["name"] == "DataComponent":
            assert cls["is_react_component"] is True
            assert any(m["name"] == "render" for m in cls["methods"])

def test_extract_react_components(js_file):
    """Test extraction of React functional components."""
    with open(js_file, 'r') as f:
        content = f.read()
    
    components = extract_react_functional_components(content)
    
    assert len(components) >= 1
    component_names = [c["name"] for c in components]
    assert "DataList" in component_names

def test_extract_typescript_interfaces(ts_file):
    """Test extraction of TypeScript interfaces."""
    with open(ts_file, 'r') as f:
        content = f.read()
    
    interfaces = extract_typescript_interfaces(content)
    
    assert len(interfaces) >= 2
    interface_names = [i["name"] for i in interfaces]
    assert "Item" in interface_names
    assert "DataProps" in interface_names

def test_process_js_file(js_file, ts_file):
    """Test the full JS/TS file processing."""
    # Test JavaScript processing
    js_result = process_js_file(js_file)
    assert "JavaScript" in js_result
    assert "import React from 'react';" in js_result
    assert "fetchData" in js_result
    assert "DataComponent" in js_result
    
    # Test TypeScript processing
    ts_result = process_js_file(ts_file)
    assert "TypeScript" in ts_result
    assert "interface Item" in ts_result
    assert "fetchData" in ts_result