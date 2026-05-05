-- Completeness
Completeness "column_name" >= 0.99

-- Uniqueness
IsUnique "column_name"

-- Value ranges
ColumnValues "score" between 0.0 and 1.0

-- String patterns
ColumnValues "email" matches "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"

-- Length constraints
ColumnLength "text" between 10 and 4096

-- Row count
RowCount between 1000 and 1000000

-- Custom SQL
CustomSql "SELECT COUNT(*) FROM primary WHERE invalid_flag = true" = 0