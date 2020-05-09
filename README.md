# TikTok

# Instructions
- Open in Google Chrome (or in any web browswer with JavaScript enabled) the TikTok profile page of interest
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
- [x] Implement Concurrency
- [] Add rotating proxies
- [] Profile crawler
- [] Trend crawler

### Install Packages
```
pip install -r requirements.txt
```

### Donate BTC
![1zdraxHPQfZ8wvpMXt2VYhnGwmkLCf7UL](https://i.imgur.com/PhC1zJG.png)
1zdraxHPQfZ8wvpMXt2VYhnGwmkLCf7UL
