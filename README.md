course-robo-era
===========

The aim of the project - easy way to download course era resources (*mp4/pdf/ppt*)
Script signIn to the courseera  class under your account, fetch class lectures and store it to specified folder.


Setup env
===========

Requirements:
* Python 2.7
* course era account

Install required libs:
<pre><code>
	python easy_install pip
	pip install -r requirements.txt
</code></pre>


Usage
===========

<pre><code>
usage: course-robo-era.py [-h] [--version] --email EMAIL --password PASSWORD --course-url COURSE_URL [--destination DESTINATION]

optional arguments:
  -h, --help            	show this help message and exit
  --version             	show program's version number and exit
  --email EMAIL         	your email on the course
  --password PASSWORD   	your password on the course
  --course-url COURSE_URL 	URL of course lectures page
  --destination DESTINATION dir where course resources will be stored (by default - current dir will be used)
</code></pre>


<pre><code>
course-robo-era.py --destination D:\temp\coursera-finance\ --email [your email on coursera] --password [your password on coursera] --course-url https://class.coursera.org/introfinance-2012-001/lecture/index
</code></pre>