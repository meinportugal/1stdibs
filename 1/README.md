# Prerequirements.

MySQL DB is created with the commands from the Categories.sql file. We are running it on a localhost with the username "user" and password "123"
It could be changed in the python script.

# Running the python script

Taking into an account that these products are not mooving fast, and not to bother the server with API requests, we believe cron job for 1-2 times a day should be enough.
As we are working directly with the API we do not need to clear the data, we only perform some basic manipulations before we write to the DB.

# Visualization

Superset is a free and powerfull tool, we use it to create a dashboard and follow the trends we see while collecting the data.

# Conclusion

Collecting the valuable data takes some time, and we do not spot significant difference during the 2 - week period. These screenshots attached show the fastest mooving category - Fashion, but it still needs some time to collect changes before we can see real differencies in the graphs. The Furniture is the biggest group (we could expect it at the antique marketplace) and changes even slower.
