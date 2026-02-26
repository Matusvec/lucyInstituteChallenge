# IQVIA database connection for R
# Run from project root. Requires: pacman, DBI, RPostgres

pacman::p_load(DBI, RPostgres)

con <- dbConnect(RPostgres::Postgres(),
                  dbname = "postgres",
                  host = "lucy-iqvia-db.c61zpvuf4ib1.us-east-1.rds.amazonaws.com",
                  port = 5432,
                  user = "student_read_only_limited",
                  password = "studentuseriqvialogin"
)

# list out all the tables
dbListTables(con)

# list out the column names in a table
dbListFields(con, "drug")
