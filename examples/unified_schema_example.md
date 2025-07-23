# Unified Database Schema Document

This document provides a comprehensive schema for the ee-productivities MongoDB database, including all collections, their relationships, field definitions, and supplementary explanations.

## Database Overview

The ee-productivities database stores application details, employee ratios, management segment tree, and DORA enabler details. The database contains multiple collections that are related through common identifiers and organizational hierarchies.

## Collections and Relationships

### 1. application_snapshot Collection

**Purpose**: Stores application details and snapshots of application states over time.

**Key Relationships**:
- Links to `employee_ratio` via `application.csiId` → `employee_ratio.csiId`
- Links to `management_segment_tree` via `application.level3` → `management_segment_tree.name`
- Links to `enabler_csi_snapshots` via `application.csiId` → `enabler_csi_snapshots.csiId`

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "snapshotId": {
      "type": "string",
      "description": "Unique identifier for the snapshot of the application."
    },
    "application": {
      "type": "object",
      "properties": {
        "csiId": {
          "type": "integer",
          "description": "Unique identifier for the application in CSI. This is the primary key for joining with other collections."
        },
        "criticality": {
          "type": "string",
          "enum": ["LOW", "MEDIUM", "HIGH"],
          "description": "Criticality level of the application. Used for filtering and analysis."
        },
        "level3": {
          "type": "string",
          "description": "Level 3 organizational unit. Links to management_segment_tree collection."
        },
        "sector": {
          "type": "string",
          "description": "Business sector of the application (e.g., 'IT', 'Finance', 'Operations')."
        },
        "status": {
          "type": "string",
          "enum": ["Active", "Inactive", "Retired"],
          "description": "Current status of the application."
        },
        "type": {
          "type": "string",
          "description": "Type of application (e.g., 'Web', 'Mobile', 'Desktop')."
        },
        "developmentModel": {
          "type": "string",
          "description": "Development model used (e.g., 'Agile', 'Waterfall')."
        },
        "hostingModel": {
          "type": "string",
          "description": "Hosting model (e.g., 'Cloud', 'On-premise')."
        }
      }
    },
    "createdAt": {
      "type": "object",
      "properties": {
        "$date": {
          "type": "string",
          "format": "date-time",
          "description": "Timestamp when the snapshot was created."
        }
      }
    },
    "year": {
      "type": "integer",
      "description": "Year of the snapshot."
    },
    "month": {
      "type": "integer",
      "description": "Month of the snapshot."
    }
  }
}
```

### 2. employee_ratio Collection

**Purpose**: Stores employee ratio details and DevHub tool adoption ratio for each user.

**Key Relationships**:
- Links to `application_snapshot` via `csiId` → `application_snapshot.application.csiId`
- Links to `employee_tree_archived` via `soeld` → `employee_tree_archived.soeld`

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "soeld": {
      "type": "string",
      "description": "SOEID of the user. This is the employee identifier."
    },
    "csiId": {
      "type": "string",
      "description": "CSI ID of the application. Links to application_snapshot collection."
    },
    "createdAt": {
      "type": "object",
      "properties": {
        "$date": {
          "type": "string",
          "format": "date-time",
          "description": "Timestamp when the document was created."
        }
      }
    },
    "employeeRatioSnapshot": {
      "type": "array",
      "description": "Snapshot of employee ratios over time.",
      "items": {
        "type": "object",
        "properties": {
          "year": {
            "type": "integer",
            "description": "Year of the ratio snapshot."
          },
          "month": {
            "type": "integer",
            "description": "Month of the ratio snapshot."
          },
          "employeeCount": {
            "type": "integer",
            "description": "Total number of employees."
          },
          "engineerRatio": {
            "type": "number",
            "description": "Ratio of engineers to total employees (0.0 to 1.0)."
          },
          "developerCount": {
            "type": "integer",
            "description": "Number of developers."
          },
          "testerCount": {
            "type": "integer",
            "description": "Number of testers."
          },
          "managerCount": {
            "type": "integer",
            "description": "Number of managers."
          }
        }
      }
    },
    "toolsAdoptionRatioSnapshot": {
      "type": "array",
      "description": "Snapshot of tool adoption ratios over time.",
      "items": {
        "type": "object",
        "properties": {
          "year": {
            "type": "integer",
            "description": "Year of the tool adoption snapshot."
          },
          "month": {
            "type": "integer",
            "description": "Month of the tool adoption snapshot."
          },
          "devhubAdoption": {
            "type": "number",
            "description": "DevHub tool adoption ratio (0.0 to 1.0)."
          },
          "gitAdoption": {
            "type": "number",
            "description": "Git adoption ratio (0.0 to 1.0)."
          },
          "ciCdAdoption": {
            "type": "number",
            "description": "CI/CD adoption ratio (0.0 to 1.0)."
          }
        }
      }
    }
  }
}
```

### 3. management_segment_tree Collection

**Purpose**: Stores organizational management segment tree structure and hierarchy.

**Key Relationships**:
- Links to `application_snapshot` via `name` → `application_snapshot.application.level3`
- Self-referencing via `parent` → `name` for hierarchical structure

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "name": {
      "type": "string",
      "description": "Name of the management segment. Links to application_snapshot.application.level3."
    },
    "hierarchy": {
      "type": "integer",
      "description": "Hierarchy level of the segment (1 = top level, 2 = second level, etc.)."
    },
    "parent": {
      "type": "string",
      "description": "Parent segment name. Self-referencing for hierarchical structure."
    },
    "year": {
      "type": "integer",
      "description": "Year of the segment data."
    },
    "month": {
      "type": "integer",
      "description": "Month of the segment data."
    },
    "version": {
      "type": "string",
      "description": "Version of the management segment structure."
    },
    "employeeCount": {
      "type": "integer",
      "description": "Total number of employees in this segment."
    },
    "budget": {
      "type": "number",
      "description": "Budget allocated to this segment."
    }
  }
}
```

### 4. employee_tree_archived Collection

**Purpose**: Stores archived employee tree structures and organizational hierarchies.

**Key Relationships**:
- Links to `employee_ratio` via `soeld` → `employee_ratio.soeld`
- Links to `management_segment_tree` via `level3` → `management_segment_tree.name`

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "soeld": {
      "type": "string",
      "description": "SOEID of the employee. Links to employee_ratio collection."
    },
    "hierarchy": {
      "type": "integer",
      "description": "Hierarchy level of the employee in the organization."
    },
    "level1": {
      "type": "string",
      "description": "Level 1 organizational unit."
    },
    "level2": {
      "type": "string",
      "description": "Level 2 organizational unit."
    },
    "level3": {
      "type": "string",
      "description": "Level 3 organizational unit. Links to management_segment_tree."
    },
    "managerSoeld": {
      "type": "string",
      "description": "SOEID of the employee's manager."
    },
    "year": {
      "type": "integer",
      "description": "Year of the employee tree data."
    },
    "month": {
      "type": "integer",
      "description": "Month of the employee tree data."
    },
    "employeeCount": {
      "type": "integer",
      "description": "Number of employees reporting to this person."
    }
  }
}
```

### 5. enabler_csi_snapshots Collection

**Purpose**: Stores DORA enabler CSI snapshots and achievement data.

**Key Relationships**:
- Links to `application_snapshot` via `csiId` → `application_snapshot.application.csiId`

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "csiId": {
      "type": "string",
      "description": "CSI ID of the application. Links to application_snapshot collection."
    },
    "enablersAggregation": {
      "type": "array",
      "description": "Aggregated enabler data over time.",
      "items": {
        "type": "object",
        "properties": {
          "year": {
            "type": "integer",
            "description": "Year of the enabler data."
          },
          "month": {
            "type": "integer",
            "description": "Month of the enabler data."
          },
          "deploymentFrequency": {
            "type": "number",
            "description": "Deployment frequency metric."
          },
          "leadTime": {
            "type": "number",
            "description": "Lead time for changes metric."
          },
          "mttr": {
            "type": "number",
            "description": "Mean Time To Recovery metric."
          },
          "changeFailureRate": {
            "type": "number",
            "description": "Change failure rate metric."
          }
        }
      }
    }
  }
}
```

### 6. statistic Collection

**Purpose**: Stores performance metrics, quality indicators, and other statistical data.

**Key Relationships**:
- Links to `application_snapshot` via `nativeID` → `application_snapshot.application.csiId`

**Schema**:
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "_id": {
      "type": "object",
      "properties": {
        "$oid": {
          "type": "string",
          "description": "Unique identifier for the document in MongoDB."
        }
      },
      "required": ["$oid"]
    },
    "nativeID": {
      "type": "string",
      "description": "Native ID of the entity. Links to application_snapshot.application.csiId."
    },
    "nativeIDType": {
      "type": "string",
      "description": "Type of the native ID (e.g., 'csiId', 'soeld')."
    },
    "statistics": {
      "type": "array",
      "description": "Array of statistical data points.",
      "items": {
        "type": "object",
        "properties": {
          "year": {
            "type": "integer",
            "description": "Year of the statistic."
          },
          "month": {
            "type": "integer",
            "description": "Month of the statistic."
          },
          "metricName": {
            "type": "string",
            "description": "Name of the metric."
          },
          "metricValue": {
            "type": "number",
            "description": "Value of the metric."
          },
          "unit": {
            "type": "string",
            "description": "Unit of measurement for the metric."
          }
        }
      }
    }
  }
}
```

## Common Query Patterns

### 1. Application Analysis
- **Find applications by criticality**: Use `application_snapshot` with filter on `application.criticality`
- **Join with employee data**: Use `$lookup` from `application_snapshot` to `employee_ratio` via `application.csiId`
- **Include management segments**: Use `$lookup` from `application_snapshot` to `management_segment_tree` via `application.level3`

### 2. Employee Analysis
- **Find employee ratios by application**: Use `employee_ratio` with filter on `csiId`
- **Join with application details**: Use `$lookup` from `employee_ratio` to `application_snapshot` via `csiId`
- **Include organizational hierarchy**: Use `$lookup` from `employee_ratio` to `employee_tree_archived` via `soeld`

### 3. Management Segment Analysis
- **Find segments by hierarchy**: Use `management_segment_tree` with filter on `hierarchy`
- **Join with applications**: Use `$lookup` from `management_segment_tree` to `application_snapshot` via `name`
- **Include employee data**: Use additional `$lookup` to `employee_ratio` via `csiId`

### 4. Performance Analytics
- **Find DORA metrics**: Use `enabler_csi_snapshots` with aggregation on `enablersAggregation`
- **Join with application context**: Use `$lookup` from `enabler_csi_snapshots` to `application_snapshot` via `csiId`
- **Include employee ratios**: Use additional `$lookup` to `employee_ratio` via `csiId`

## Key Field Relationships

| From Collection | From Field | To Collection | To Field | Relationship Type |
|----------------|------------|---------------|----------|-------------------|
| application_snapshot | application.csiId | employee_ratio | csiId | One-to-Many |
| application_snapshot | application.csiId | enabler_csi_snapshots | csiId | One-to-One |
| application_snapshot | application.level3 | management_segment_tree | name | Many-to-One |
| employee_ratio | soeld | employee_tree_archived | soeld | One-to-One |
| employee_tree_archived | level3 | management_segment_tree | name | Many-to-One |
| statistic | nativeID | application_snapshot | application.csiId | Many-to-One |

## Data Types and Constraints

### Criticality Levels
- **LOW**: Non-critical applications
- **MEDIUM**: Moderately critical applications  
- **HIGH**: Highly critical applications

### Status Values
- **Active**: Currently in use
- **Inactive**: Temporarily suspended
- **Retired**: No longer in use

### Engineer Ratio
- Range: 0.0 to 1.0
- Represents the proportion of engineers to total employees

### Hierarchy Levels
- **1**: Top-level organizational units
- **2**: Second-level organizational units
- **3**: Third-level organizational units (most common for applications)

## Performance Considerations

1. **Indexing**: The `csiId` and `soeld` fields are frequently used for joins and should be indexed
2. **Aggregation Limits**: Use `$limit` in aggregation pipelines to prevent large result sets
3. **Join Order**: Start with the smallest collection when possible to optimize join performance
4. **Projection**: Use projection to limit returned fields and improve performance

## Common Filtering Patterns

### Date-Based Filtering
```javascript
// Filter by year and month
{"year": 2024, "month": 6}

// Filter by date range
{"createdAt.$date": {"$gte": "2024-01-01", "$lte": "2024-12-31"}}
```

### Status-Based Filtering
```javascript
// Active applications only
{"application.status": "Active"}

// High criticality applications
{"application.criticality": "HIGH"}
```

### Employee Ratio Filtering
```javascript
// Applications with good engineer ratios
{"employeeRatioSnapshot.engineerRatio": {"$gte": 0.7}}
```

This unified schema provides a comprehensive view of the database structure, relationships, and common query patterns for the ee-productivities MongoDB database. 