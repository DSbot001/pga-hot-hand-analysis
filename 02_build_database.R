library(DBI)
library(RSQLite)
library(dplyr)

results <- readRDS("holes_2025_raw.rds")

# Report events with no downloaded records.
failed <- names(results)[
  sapply(results, function(x) is.null(x) || nrow(x) == 0)
]

message(
  "Events with no data: ",
  if (length(failed)) paste(failed, collapse = ", ") else "none"
)

# Combine events and retain the event name for each record.
all_holes <- bind_rows(results, .id = "event_query")

# Report missing values without removing any records.
missing_values <- data.frame(
  attribute = names(all_holes),
  n_missing = colSums(is.na(all_holes)),
  row.names = NULL
)
print(missing_values)

# Store the raw records in SQLite.
pga_db <- dbConnect(SQLite(), "pga_2025.sqlite")
dbWriteTable(pga_db, "all_holes", all_holes, overwrite = TRUE)

# Drop full-line comments before splitting SQL into individual statements.
sql_lines <- readLines("analysis.sql")
sql_lines <- sql_lines[!grepl("^\\s*--", sql_lines)]
sql <- paste(sql_lines, collapse = "\n")

for (statement in strsplit(sql, ";")[[1]]) {
  if (nzchar(trimws(statement))) {
    dbExecute(pga_db, statement)
  }
}

# Check the final sample size and close the connection.
dbGetQuery(pga_db, "SELECT COUNT(*) AS n_holes FROM analysis")
dbDisconnect(pga_db)
