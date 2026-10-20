HOLD'EM TABLE: PHONE APP SETUP

The game is a web app. It has to be hosted once at an https address,
then you add it to your home screen. After that it opens full screen
like a regular app, works offline, and keeps your save on your phone.

1. Put it online (free, about 2 minutes)
   - On a computer, go to https://app.netlify.com/drop
   - Unzip holdem-table.zip and drag the holdem-table folder onto that page.
   - Netlify gives you a link like https://something.netlify.app
     (Make a free account when it asks if you want the link to stay up.)

2. Install on your phone
   - iPhone: open the link in Safari, tap Share, then Add to Home Screen.
   - Android: open the link in Chrome, tap the menu, then Install app
     (or Add to Home screen).

3. Bring your progress over from the Claude version
   - In the Claude version: Settings tab, Backup and transfer,
     Show save code, then copy it.
   - In the phone app: Settings tab, paste into the box, Restore from code.

Notes
   - Your save lives on the phone, inside the installed app. Deleting the
     app deletes the save, so use Download backup now and then.
   - To update the game later, replace index.html in the folder, change
     VERSION in sw.js (holdem-v1 to holdem-v2), and drag the folder to
     Netlify again. The app updates the next time it opens with internet.
