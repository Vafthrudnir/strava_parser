# strava_parser
parsers strava for recent activities

# Usage
Run host.sh to host the site, than visit the offered authorization URL to make the site save your access data.

For hosting the client secret will be required (https://www.strava.com/settings/api), which is parsed from a simple text file stored in application root named 'client_secret'.

The full refresh page is also password protected to avoid accidental triggering (as it dumps a heavy load on the API). To set the password create a file called 'refresh_password' in the application root.
