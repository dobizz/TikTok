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