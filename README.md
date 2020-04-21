# TikTok

# Instructions
- Open in Google Chrome the TikTok profile page of interest
- Press F12 and go to the console tab.
- Copy the contents of chrome_console_script.js, paste to console, and run
```
(function() {
    var links = $$('a');
    var video_urls = [];
  
  // Loop through all links
    for (index in links) {
        var url = links[index].href;
        
        // loop through all links and check for videos
        if (url.indexOf('video') > -1) {
            // store links in variable
            video_urls.push(url);
            // output to console
            console.log(url);
        }
    }
    // create text document and save links
    var textDoc = document.createElement('a');

    textDoc.href = 'data:attachment/text,' + encodeURI(video_urls.join('\n'));
    textDoc.target = '_blank';
    textDoc.download = 'videolist.txt';
    textDoc.click();
})();
```
- This will download the 'videolist.txt', copy this text file to the same driectory as video_crawler.py
- Run video_crawler.py and wait for script to finish.
```
python video_crawler.py
```

## chrome_console_script.js
JavaScript to run in Google Chrome console in order to generate the video urls and save to 'videolist.txt' for a particular profile.

## video_crawler.py
Python3 based script to go through the video urls in 'videolist.txt' and download to ./videos/[tiktok_username] directory.

### Work In Progress
- Add rotating proxies.
- Add threading support to make downloads faster, if you have the bandwidth.

### pips
```
pip install -r requirements.txt
```
or manually install each package
```
pip install beautifulsoup4
pip install lxml
pip install requests
```
