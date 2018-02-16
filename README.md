# Ud-FSND-LinuxServerConfiguration
Udacity Full Stack Web Developer Nanodegree Project : Linux Server Configuration

## Skills Honed
1. Python
2. HTML
3. CSS
4. OAuth
5. Flask Framework
7. Apache web server creation/security
8. Using Amazon light Sail
9. Hosting Website from Scratch.

## IP address and SSH port
* Public IP : ~34.201.42.231~
* SSH port : ~2200~

## Complete URL to hosted web application
~http://34.201.42.231.xip.io/~


## About
This project is About How to Create Web Server from scatch and how to setup firewalls, running a  RESTful web application utilizing the Flask framework which accesses a SQL database that populates categories and their items. OAuth2 provides authentication for further CRUD functionality on the application. Currently OAuth2 is implemented for Google Accounts. This Project is Hosted on Amazon light sail.

## In This Repo
This project has one main Python module `application.py` which runs the Flask application. A SQL database is created using the `modal.py` module and you can populate the database with test data using `filldb.py`.
The Flask application uses stored HTML templates in the tempaltes folder to build the front-end of the application. CSS/JS/Images are stored in the static directory.



## Summary of software installed and installation instruction.

### Setup Your Amazon Light sail account and creat a ununtu 16.04 virtual machine.
- https://lightsail.aws.amazon.com/ls/webapp/home/instances
- SSh into our virtual machine 

### Update all currently installed packages
- One of the most important and simplest ways to ensure your system is secure is to keep your software up to date with new releases
- when setting up a new machine, you can be pretty safe in just accepting that the system is always making the best decisions for you
```bash
sudo apt update     # update available package lists
sudo apt upgrade    # upgrade installed packages
sudo apt autoremove # automatically remove packages that are no longer required
```
### Create a New User `grader` and give `grader` sudo
 - Log in to your server as the root user.
```bash
sudo adduser grader # create a new user named grader
# grader password is 'grader'
# use the usermod command to add the user to the sudo group
# https://www.digitalocean.com/community/tutorials/how-to-create-a-sudo-user-on-ubuntu-quickstart
sudo usermod -aG sudo grader
# test new user can use sudo
# Login as Grader
su - grader
sudo ls -la /root  # will be prompt for password only one time.
# if working you can see the content of /root directory.
```

### Change the SSH port from 22 to 2200.
# do
```bash
sudo nano /etc/ssh/sshd_config  # change port 22 to 2200
sudo service ssh restart        # restart ssh service
```

### Configure the Firewall (UFW) to only allow incoming connections for SSH (port 2200), HTTP (port 80), and NTP (port 123).
- Warning: When changing the SSH port, make sure that the firewall is open for port 2200 first, so that you don't lock yourself out of the server.
- When you change the SSH port, the Lightsail instance will no longer be accessible through the web app 'Connect using SSH' button. The button assumes the default port is being used. 
```bash
sudo ufw status                 # check ufw status 
sudo ufw default deny incoming  # initially block all incoming requests
sudo ufw default allow outgoing # default rule for outgoing connections
sudo ufw allow 2200/tcp         # allow SSH on port 2200
sudo ufw allow www              # allow HTTP on port 80
sudo ufw allow ntp              # allow NTP on port 123
sudo ufw enable                 # enable firewall
sudo ufw status                 # check ufw status
```

### Create an SSH key pair for grader using the ssh-keygen tool
```bash
# local machine
ssh-keygen 
# Enter file in which to save the key (/home/bcko/.ssh/id_rsa): grader
# empty passphrase
```

```bash
cd ~ # takes you to your home directory /home/grader
sudo mkdir .ssh   # Directory where you will later store your public key.
sudo chown grader:grader .ssh # changing ownership of .ssh to grader
sudo chmod 700 .ssh           # change folder permission
sudo touch /.ssh/authorized_keys #creates a file to put your public key in.
sudo chmod 644 /.ssh/authorized_keys #change file permission
```

```bash
# Setup your shh, on your choice of ssh platform like Putty.
~ https://devops.profitbricks.com/tutorials/use-ssh-keys-with-putty-on-windows/ ~ # link to setup shh with using private key on putty.

   grader@34.201.42.231 port:2200  
```

### Disable root
```bash
sudo nano /etc/ssh/sshd_config  # open sshd_config
# change PermitRootLogin to no
sudo service ssh restart        # restart ssh service
```
### Configure the local timezone to UTC.
```bash
# https://www.digitalocean.com/community/tutorials/how-to-set-up-time-synchronization-on-ubuntu-16-04
sudo timedatectl set-timezone UTC
```

### Install Apache and mod_wsgi for python 2.7

```bash
sudo apt install apache2                  # install apache- A Web server
- If done right go to the public ip address of your lightsail and you should see apache default page.
sudo apt-get install libapache2-mod-wsgi  # install python 2.7 mod_wsgi
```



### Install and configure PostgreSQL
```bash
sudo apt install postgresql                    # install postgreSQL 
sudo nano /etc/postgresql/9.5/main/pg_hba.conf # no remote connections to the database
# Create a new database user named catalog that has limited permissions to your catalog application database.
sudo -u postgres createuser -P catalog


```

### Clone and setup your Item Catalog project from the Github repository in Ubuntu user. 
```bash
sudo apt install git # Install git
cd /var/www    # go to apache directory to place your project
sudo git clone https://github.com/amanueln/catalogs.git # clone project into /var/www/ 

```

### create .wsgi file
```bash
nano catalog.wsgi  # place file in /var/www/catalogs/

### setup your wsgi
#!/usr/bin/python3
import sys
sys.path.insert(0,"/var/www/catalogs/")  # tell apache where your application is

from application import app as application
application.secret_key = 'super_secret_key'


```
# sudo a2enmod wsgi
 - enables wsgi Apache module.

### configure Apache to handle requests using the WSGI module
```bash
cd /etc/apache2/sites-enabled
sudo touch FlaskApp.conf  # create a custome .conf file to handle requests.
sudo nano FlaskApp.conf  
```


```
<VirtualHost *:80>
        # The ServerName - directive sets the request scheme, hostname and port that
        # the server uses to identify itself. This is used when creating
        # redirection URLs.In the context of virtual hosts, the ServerName-
        # specifies what hostname must appear in the request's Host: header to
        # match this virtual host. 

    ServerName http://ec2-34-201-42-231.compute-1.amazonaws.com
    ServerAdmin nathanielamanuel@gmail.com
    WSGIScriptAlias / /var/www/catalogs/catalog.wsgi
  <Directory /var/www/catalogs/>
        Order allow,deny
        Allow from all
  </Directory>
    ErrorLog ${APACHE_LOG_DIR}/error.log
    LogLevel warn
    CustomLog ${APACHE_LOG_DIR}/access.log combined

</VirtualHost>
```

### Install Flask and dependencies
```bash
sudo apt install python-pip
sudo pip install httplib2
sudo pip2 install sqlalchemy flask-sqlalchemy psycopg2 bleach requests
sudo pip2 install flask packaging oauth2client redis passlib flask-httpauth
```

### If any issues check your developer consule and Apache2 erro log
# sudo cat /var/log/apache2/error.log


## Dependencies
- [Putty](https://devops.profitbricks.com/tutorials/use-ssh-keys-with-putty-on-windows/)
- [Amazon Lightsail](https://lightsail.aws.amazon.com)
- [Udacity forum Help](https://discussions.udacity.com/t/linux-server-configuration-amazon-lightsail-localhost-setup/583077)
- [Google Cloud platform](https://console.cloud.google.com/home/dashboard?project=my-project-1501372871219)


*Optional step(s)

## Using Google Login:
# if issue with logn:
To get the Google login working there are a few additional steps:

1. Go to [Google Dev Console](https://console.developers.google.com)
2. Sign up or Login if prompted
3. Go to Credentials
4. Select Create Crendentials > OAuth Client ID
5. Select Web application
6. Enter name 'Item-Catalog'
7. Authorized JavaScript origins = 'http://34.201.42.231.xip.io/' 
8. Authorized redirect URIs = 'http://34.201.42.231.xip.io/'
9. Select Create
10. On the Dev Console Select Download JSON
11. Rename JSON file to 'client_secrets.json'
12. Place JSON file in catalogs directory that you cloned from git.


## JSON Endpoints
The following are open to the public:

Catalog JSON: `/catalog/JSON or /JSON`
    - Displays all Categories.


Category Items JSON: `/catalog/<int:catalog_id>/items/JSON`
    - Displays items for a specific category

