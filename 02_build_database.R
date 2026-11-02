library(DBI)
library(RSQLite)
library(dplyr)

results <- readRDS("holes_2025_raw.rds")

# Events that failed to download (NULL or 0 rows)
failed <- names(results)[sapply(results, function(x) is.null(x) || nrow(x) == 0)]
message("Events with no data: ", if (length(failed)) paste(failed, collapse = ", ") else "none")

# Stack all events into one table; failed events are skipped automatically
all_holes <- bind_rows(results, .id = "event_query")

pga_db <- dbConnect(SQLite(), "pga_2025.sqlite")
dbWriteTable(pga_db, "all_holes", all_holes, overwrite = TRUE)

# dbExecute runs one statement at a time, so split the SQL file on semicolons.
# Strip "--" comments first so a semicolon inside a comment can't break a statement.
sql_lines <- sub("--.*$", "", readLines("analysis.sql"))
sql <- paste(sql_lines, collapse = "\n")
for (statement in strsplit(sql, ";")[[1]]) {
  if (nzchar(trimws(statement))) dbExecute(pga_db, statement)
}

dbGetQuery(pga_db, "SELECT COUNT(*) AS n_holes FROM analysis")
dbDisconnect(pga_db)