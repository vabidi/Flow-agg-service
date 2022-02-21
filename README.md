
# INSTRUCTIONS

Prerequisites:
   - ubuntu 18.04.4
   - python 3.6.9
   - django 3.2.12

1. Clone the git repo from github.com/vabidi/Flow-agg-service

2. Modify firewall rules and security-groups to open the server port, if
   needed. 

   For example: `sudo ufw allow 8000`

3. Run the server
   `python manage.py server 0.0.0.0:8000`



# DESIGN

I decided to use Python and Django for this exercise, because it could be 
coded up rapidly to get a first cut, and to evaluate design choices for further
improvements.

HTTP Requests are handled by Django's built-in lightweight web server. 
Based on the urlpattern specified in fas/urls.py, they are dispatched to
handlers in file fas/views.py.

Code in fas/views.py has the logic to handle GET and POST requests.

For this exercise I used the default SQLite database.  For the next version, we
should use a more scalable database like PostgreSQL.

In Django, the database layout is abstracted into 'models'.  
Each model is represented by a class that subclasses django.db.models.Model.   
A model has a number of class variables, each of which represents a database field in the model.  

For this exercise, there is single model - class Flowlog.  
It is defined in fas/models.py

The primary key is a tuple (src_app, dest_app, vpc_id, hour).  
Django does not support multi-column keys.   
Therefore, we create a unique 'hashkey' by concatenating the 4 values.  
A drawback is that this new column uses additional, redundant storage in the
database.

  **POST Handler**

  Find object matching the given values of (src_app, dest_app, vpc_id, hour)  
  If object exists, update the values of bytes_tx and bytes_rx, and save it
  back to the database.  
  If object does not exist, create a new object and save it to database.

 **GET Handler**

  Find all objects matching the given value of 'hour'.  
  Return all fields of matching rows, except the 'hashkey'.

# STORAGE CONSIDERATIONS

In this submission, the code enforces a maximum limit on the number of flow
records saved. 

The database will eventually fill up.  
We need a policy for how to free up space in the database.  
For the flow aggregation application, one approach would be to run a periodic
job to move all flow-logs older than a particular 'hour' value into a separate
archive. The would be done once a day,  once a week, etc.  
Flow logs can also be aggregated into buckets with different granularities, for example, a 4-hour bucket, a 24-hour bucket, etc.



# PERFORMANCE CONSIDERATIONS

 Use a nginx/gunicorn frontend for better performance, scaling, load-balancing,
security.

 Use a more performant database like PostgreSQL.

 Django has support for many web-servers and databases.

 Do performance benchmarking to see if using a string as primary key is
expensive. Maybe a database schema with two tables, and integer key will be
more efficient.

Django is probably not the best framework for this application.  
For production, a time-series database would be better.  
I would look at design ideas from OpenTSDB.


# SCALING CONSIDERATIONS

Scale out with multiple workers. 



# TEST WITH Example Data

Following is a screen capture from tests I did with the supplied example data.  
Note that, compared to the example data,  I modified the values of 'hour' to 91, 92, 93.  
Also, I added quotes around src_app and dest_app.  

```
root@systest-runner:~/testfas[21674]# more flexample_data 
[
{"src_app": "foo", "dest_app": "bar", "vpc_id": "vpc-0", "bytes_tx": 100, "bytes_rx": 500, "hour": 91},
{"src_app": "foo", "dest_app": "bar", "vpc_id": "vpc-0", "bytes_tx": 200, "bytes_rx": 1000, "hour": 91},
{"src_app": "baz", "dest_app": "qux", "vpc_id": "vpc-0", "bytes_tx": 100, "bytes_rx": 500, "hour": 91}, 
{"src_app": "baz", "dest_app": "qux", "vpc_id": "vpc-0", "bytes_tx": 100, "bytes_rx": 500, "hour": 92}, 
{"src_app": "baz", "dest_app": "qux", "vpc_id": "vpc-1", "bytes_tx": 100, "bytes_rx": 500, "hour": 92}
]

root@systest-runner:~/testfas[21674]# curl -X POST http://perfrunner-1:8000/fas/flows --insecure -H "Content-Type: application/json" --data @flexample_data 

root@systest-runner:~/testfas[21672]# 
root@systest-runner:~/testfas[21672]# curl  http://perfrunner-1:8000/fas/flows?hour=91 --insecure 
[{"src_app": "foo", "dest_app": "bar", "vpc_id": "vpc-0", "bytes_tx": 300, "bytes_rx": 1500, "hour": 91}, {"src_app": "baz", "dest_app": "qux", "vpc_id": "vpc-0", "bytes_tx": 100, "bytes_rx": 500, "hour": 91}]

root@systest-runner:~/testfas[21673]# curl  http://perfrunner-1:8000/fas/flows?hour=92 --insecure 
[{"src_app": "baz", "dest_app": "qux", "vpc_id": "vpc-0", "bytes_tx": 100, "bytes_rx": 500, "hour": 92}, {"src_app": "baz", "dest_app": "qux", "vpc_id": "vpc-1", "bytes_tx": 100, "bytes_rx": 500, "hour": 92}]

root@systest-runner:~/testfas[21674]# 
root@systest-runner:~/testfas[21674]# curl  http://perfrunner-1:8000/fas/flows?hour=93 --insecure 
[]

root@systest-runner:~/testfas[21675]#
```




# CHALLENGES FACED

 It took some time and effort to setup the Django environment.  
 Fortunately, the Django documentation is very good, and stackoverflow had
solutions to problems I encountered during install.

# TODO

 - Add logging messages
 - Add unit tests


# REFERENCES
 1. Django docs  https://docs.djangoproject.com/
 2.  stackoverflow  
