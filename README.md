Instructions and example code for creating a chatbot for any chat that Beeper supports - currently iMessage, Twitter, Instagram, Facebook, Whatsapp, Telegram, Slack, Discord, Signal , and Linkedin

Requirements:
- Be a Beeper user
- Python > 3.7
- Docker
- yarn

## 1. Getting a Maubot running

1. following [these steps](https://docs.mau.fi/maubot/usage/setup/docker.html) I ran the docker container to create a Maubot server on my local machine
    1. an unspoken but relevant step here is to create a user that you’ll log into your Maubot Manager interface with. do this line 86 of `config.yaml`. For example 
        1. `myUser: somePasswordHere`
    2. re-run the docker container after that and you should be able to visit [`http://localhost:29316/_matrix/maubot`](http://localhost:29316/_matrix/maubot) and login with the above user
2. next I created a dummy matrix account - this is the identity that my first bot will use to send messages on the matrix network.
    1. navigate to [app.element.io](http://app.element.io/), and create a new account. call it `yournameTestBot` or something
3. then I connected my maubot server to my dummy matrix account
    1. you’ll need to install the maubot cli for this. keep the your docker container running, and in the same directory that you started your docker container from, run steps 1-3 of “Production Setup” [here](https://docs.mau.fi/maubot/usage/setup/index.html) to install the cli
    2. run `mbc login` and use the credentials that you created in your `config.yaml`
    3. run `mbc auth` . use “matrix.org” as the homeserver, and use the username and password for your dummy matrix account on [element.io](http://element.io). take note of the output, you’ll need it in a sec.
    4. in a different directory, clone the [echo bot](https://github.com/maubot/echo) plugin. any [maubot plugin](https://github.com/maubot) would have worked here, but echo is simple and lightweight so it makes a good starting point. after cloning,  run `zip -9r plugin.mbp *` to compile it into the necessary file format for uploading.
    5. then I opened [`http://localhost:29316/_matrix/maubot`](http://localhost:29316/_matrix/maubot) and connected the dots. 
        1. Click plugins on the sidebar and upload `plugin.mpb` from your echo directory
        2. Click clients on the sidebar 
            1. your User ID you can grab from your [element.io](http://element.io) account - it’ll be `@yournameTestBot:matrix.org` if you’re following the same format I am
            2. Homeserver should be matrix.org
            3. Fill in access token and device ID from the output of the `mbc auth` command above
            4. Pick whatever display name you’d like and save!
        3. Click instances in the sidebar and name give it whatever ID you’d like. Then make the primary user the client you just created, and make the type the plugin you’ve uploaded. Save that
    6. ok so my test bot was actively running on the matrix network - now I wanted to interact with it
        1. in beeper, create “new beeper chat” (command k → new beeper chat) then search for the user id of the client you set up - `yournameTestBot:matrix.org` if you’re following my format)
        2. it should populate with the display name of that bot. click that, start a chat, and type !ping
        3. in [element.io](http://element.io), you should be able to see the !ping message you sent from beeper come through to your matrix account. your bot should automatically respond with the corresponding “pong” back. 

## 2. Running it on iMessage

ok - the echo bot is now effectively receiving and sending messages from my dummy matrix account. now I want it to do the same from my beeper account

1. edit the `config.yaml` to include [beeper.com](http://beeper.com) as a homeserver. IE the `homeservers` block in your config file should look like:
    
    ```yaml
    homeservers:
        beeper.com:
            url: https://matrix.beeper.com
        matrix.org:
            url: https://matrix-client.matrix.org
    ```
    
2. re-run `mbc auth` and this time use [beeper.com](http://beeper.com) as the homeserver. use your beeper username and password to login. take note of the output
3. restart your docker container `docker run --restart unless-stopped -p 29316:29316 -v $PWD:/data:z dock.mau.dev/maubot/maubot:latest`
4. go to your matrix manager in your browser 
    1. create a new client. use [beeper.com](http://beeper.com) as the homeserver (it should appear in the dropdown), and input the access token and device ID from the output of `mbc auth` use whatever you like for the id, but note that when people find you on beeper, this id and display name will show up
    2. create a new instance. use whatever id you like, and connect it from your new beeper client to the existing echo bot plugin
5. send yourself an iMessage “!ping” and your bot will attempt to respond, but fail. it needs to be verified.
    1. do this by going into beeper, cmd k → “new beeper chat” and type in any username (doesn’t matter you won’t actually send them anything)
    2. click “info” in the top right → “people” and then click to verify the maubot instance running with your account credentials.
6. try again and you should find that you respond to anyone who iMessages you “!ping”  with “!pong”, without you typing anything! 

## 3. Customizing it

ok - time to actually build my bot. I used the echo bot as a starting point and sourced some inspiration from the other [maubot plugins](https://github.com/maubot) where necessary. here are my general tips for building a beeper-connected maubot

1. set up your python editing environment so that it can read the maubot python package. this ended up being critical because the auto-complete suggestions were more helpful than the documentation in many cases
2. I found reverse engineering most helpful in my case. IE: use beeper to send an iMessage with the format I’m aiming for (a photo with no text). then in beeper, right click the message → view source and try to find the API calls that seem like thye would produce that payload.
3. when in doubt, read the docs [here](https://matrix-org.github.io/matrix-python-sdk/) for the matrix python sdk 
4. [here](https://github.com/clearspace-team/iMessage-bot/blob/main/bot.py)’s the source code that I ended up with to run my bot

    

## 4. Hosting it

Once I had everything working from the docker container running on my laptop, I just needed to get this hosted somewhere that was permanently online. 

1. spin up a new ec2 instance on AWS - make sure to allow http and https connections in the settings when you are creating it
2. `ssh` into it and install python, docker, and yarn
    1. I don’t remember the exact commands here, but it was the expected dance with trial, error, and google search while blind-firing `sudo yum` commands from the hip
3. create a `maubot` directory on your ec2 box, and follow maubot’s [docker steps](https://docs.mau.fi/maubot/usage/setup/docker.html), as well as steps 1-3 of “[Production setup](https://docs.mau.fi/maubot/usage/setup/index.html)” to install the `maubot-cli`
4. expose the Maubot Manager web UI that your ec2 is hosting. 
    
    (there is almost certainly a more graceful way to do this using the `config.yaml` file, but the goal line was in sight, so here’s what I went with.)
    
    1. signed up for an [ngrok](https://ngrok.com/) account and downloaded the [linux installation](https://ngrok.com/download) on my laptop
    2. unzipped the file and scp’ed the binary into my ec2 instance 
        1. `scp -i "path/to/ec2_keys.pem" ~/Downloads/ngrok ec2-user@ec2-IP-ADDRESS.us-east-2.compute.amazonaws.com:~/`
    3. authed with ngrok with the account I just signed up for 
        1. `ngrok config add-authtoken myToken`
    4. created a tunnel to port `29316` where my docker was running the Maubot Manager
        1. `ngrok http 29316`
    5. copy and paste the http**s** URL that ngrok generates (makes sure https not http) and append /_matrix/maubot to it in your laptop browser
    6. upload your plugin, create a client and an instance using your beeper credentials - just as before, and you’re in business! your maubot can send and receive messages on your behalf regardless of whether you’re online or not.
