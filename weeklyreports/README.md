
Usage
-----
```console
usage: weeklyreport.py [-h] [--config_file CONFIG_FILE] [--profile PROFILE]
                       [--year YEAR] [--week WEEK] [--all_reports]
                       [--auth_host_name AUTH_HOST_NAME]
                       [--noauth_local_webserver]
                       [--auth_host_port [AUTH_HOST_PORT [AUTH_HOST_PORT ...]]]
                       [--logging_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

optional arguments:
  -h, --help            show this help message and exit
  --config_file CONFIG_FILE
                        Weekly report configuration file.
  --profile PROFILE     Name of the profile to run defined in the
                        configuration file.
  --year YEAR           Year the weekly report is in.
  --week WEEK           Week number of report.
  --all_reports         Generate all reports.
  --auth_host_name AUTH_HOST_NAME
                        Hostname when running a local web server.
  --noauth_local_webserver
                        Do not run a local web server.
  --auth_host_port [AUTH_HOST_PORT [AUTH_HOST_PORT ...]]
                        Port web server should listen on.
```
Configuration File Parameters
-----------------------------
```yaml
# Setup profiles for different reports you might run.
profiles:
  run:
    spreadsheet: <google sheet id>
    folder: <google folder id>
    image_folder: <google folder id>
    image_alt_text: Embeded images are not supported in your email client. Open the above google document to see this image.
    from: First Last <flast@example.com>
    bcc: group@example.com, person@example.com, another@example.com
  test:
    spreadsheet: <google sheet id>
    folder: <google folder id>
    image_folder: <google folder id>
    image_alt_text: Embeded images are not supported in your email client. Open the above google document to see this image.
    from: First Last <flast@example.com>
    to: user+totest@example.com
    cc: user+cctest@example.com
    bcc: user+bcctest@example.com

# Ordered list of report topics in google spread sheet. All topics not listed here will be appended to the bottom of the status report.
reports:
  - Water Shed
  - Apple Tree
```

Google sheet format
-------------------

| Year | Week | Person | Project | Status | Rollup |
| ---- | ---- | ---- | ---- | ---- | ---- | 
| 2017 | 14 | Joe | Apple Tree | Raw status from Joe 1<br/>Raw status from Joe 2<br/>Raw status from Joe 3<br/>Raw status from Joe 4<br/>Raw status from Joe 5<br/> | Pretty status from Joe 2<br/>Pretty status from Joe 4<br/>Pretty status from Joe 5<br/> |
| 2017 | 14 | Joe | New Soil | Raw status from Joe | Pretty status from Joe |
| 2017 | 14 | Joe | Water Shed | Raw status from Joe | |
| 2017 | 14 | Bob | Apple Tree | Raw status from Bob | Pretty status from Bob |
| 2017 | 14 | Bob | New Soil | Raw status from Bob | |
| 2017 | 14 | Bob | Water Shed | Raw status from Bob | #### Header Name<br/>Pretty status from Bob<br/>\![][testurlimage]<br/>Another pretty status from Bob<br/>\![Custom alt img tag here][image1]<br/>[image1]: image1.png "This text will show on mouse hover"<br/>[testurlimage]: https://cdn.pixabay.com/photo/2014/06/03/19/38/road-sign-361513_640.jpg "This text will show on mouse hover" |
| 2017 | 14 | Jake | Landfill | Raw status from Jake | Pretty status from Jake<br/>    - Bullted item 1<br/>    - Bulleted item 2 |


Markdown formatting
-------------------
### Images
`alt text` is optional if left blank: `![][image_reference]`, `image_alt_text` configured in the configuration file will be used. If `image_alt_text` is not configured, the `alt` tag will be left blank.
```markdown
![alt text][image_reference]
[image_reference]: <URL|image_name> "<mouse over text"
```
