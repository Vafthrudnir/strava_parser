docker run -d --name strava_parser -v /$(pwd)/save_data:/usr/src/app/save_data -p 80:5000 strava_parser
