osascript -e 'tell app "Terminal"
    do script "cd /Users/ztc0611/Documents/GitHub/shared-folders && python3 server.py"
    do script "cd /Users/ztc0611/Documents/GitHub/shared-folders && python3 client.py"
end tell'