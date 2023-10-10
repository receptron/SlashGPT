install on mac

```
brew install pgvector
brew tap homebrew/core
brew install postgresql
brew services start postgresql
```

connect postgres

```
psql -h localhost -p 5432 -U isamu -d postgres
```

create and setup db
```
create extension if not exists vector;
create database test_vector;
```

connect new db
```
psql -h localhost -p 5432 -U isamu -d test_vector
```

create table

```
CREATE TABLE IF NOT EXISTS vector_table
                 (id SERIAL NOT NULL,
                  embedding VECTOR(1536),
                  text varchar(8192), fileName varchar(2048),
                  pageNumber integer, PRIMARY KEY (id));
```

install pip
```
pip install pgvector psycopg
```
