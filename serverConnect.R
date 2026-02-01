pacman::p_load(DBI,RPostgres)

con <- dbConnect(RPostgres::Postgres(),
                  dbname = "postgres",
                  host = "lucy-iqvia-db.c61zpvuf4ib1.us-east-1.rds.amazonaws.com",
                  port = 5432,
                  user = "student_read_only_limited",
                  password = "studentuseriqvialogin"
)

dbListTables(con)

dbListFields(con, "drug")  # replace "your_table_name" with an actual table name to see its fields

rs <- dbSendQuery(con, "SELECT * FROM drug")  # replace "your_table_name" with an actual table name

drug <- dbFetch(rs)


write.csv(drug, "drug.csv")