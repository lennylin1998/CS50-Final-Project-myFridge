# myFridge
### Video Demo
[https://youtu.be/4kYQCsVjIjM](https://youtu.be/jgsUILGJUPg)
### Motivation
My grandmother has a habbit of buying too much food and stuffing all of them in the fridge. Sometimes the food goes straight to the bin because we forget about it and leave it in the fridge for too long. So I want to build an app to help me keep track of the items in fridge, so that I can cook the nearly overdue food to avoid food waste.
### Main Functionality
1. To record every grocery shopping purchases
2. To keep track of items in fridge, showing how manys days left until they go expired
3. To create one's own recipe
4. To allow for searching recipe by either its name or ingredient
5. To allow for editing an existing recipe
6. To show history, including cooking, recipe creation, purchase, and items that are overdue
### Dtail Explanation
#### /static
**scripts.js** - I have all the Javasript/ jQuery code in this file, and then add it as an extension into the HTML file to keep the code clean.

First, I use ".click()" to create a extendable list throughout the web app. The plus icon would insert a identical row below, and the minus icon would delete the whole row. Here I found that I have to use "event.stopPropagation()" to stop event from bubling. Also, because it is extendable, I have to use a loop to increment on the number of rows and give "name attribute" after it, to make sure we can know what does the input contains. For example the first row would contain inputs with name attribute of 'itm-0' (stands for item's name), 'cat-0' (stands for its category), 'qty-0' (stands for its quantity), 'uni-0' (stands for its unit), 'psd-0' (stands for its purchase date), and 'bsb-0' (stands for its best-before date). The second row would follow the same logic except it would increment on the number. I use this method whenever I have multiple forms on the webpage but I need to differentiate them on the backend.

Next is the DataTable configuration. This is a huge part of my project because it took me some time to find a beautiful interactive plug-ins for table, and it took me even longer to explore the documentation of it. But once got my hands on it, I found it easy to customize the table to cater my need. I like its search function the most, it is default yet so powerful. In the middle of my exploration, I actually found that I can use DataTable's API to connect to my sqilte databse directly, but I eventually give up for that I need to pay for that API functionality.

Also, I add some event listener to allow better user experience. For example, the cook button on the recipe page would be disabled if one doesn't have enough ingredient in his fridge. The same applies to the button on the fridge page when no item is selected.

Finally, I use AJAX through jQery syntax, to had ingredients pop up on page whenever a recipe is clicked or searched for. Initially I want to configure the look as child rows, with ingredients being collapsable. but later I found it not feasible for the same pay-to-use problem as mentioned above. That is why I turn to ajax call and cerate a separate HTML file for it.

**styles.css** - This file contains bisc css font/ color configuration.

#### /templates
This file contains all the HTML files. The design of this app is similar to that of pset 9, where we have an layout as default setup, and almost all the pages are extended from it. Except that the login and logout page have their own layout.

**app.py** - This is the file where I use flask to handle request in backend. I use sqlite3 as my database, and utilize the sqlite3 package in python to connect to it ,and execute queries. I choose sqlite because it is easily configured and doesn't require any account.

**myfridge.db** - The database file.
The problem of the database design is that I can have the same item purchased multiple times. For example I could have purchase chicken today, and purchase another chicken two days later. To solve this problem, I create two table, "items" and "purchase". The table "items" stores information about the item overall, the name and the unit. Those are the info that doesn't change at all. The "purchase" table stores info specific to "that" purchase, the purchase date and best-before date. This way the fridge can display the items by its 'purchase_id', and the recipe page would display the ingredients by its 'item_id' (Since the ingredients require just "chicken" rather "the chicken I bought on 2022-05-30"). The quantity on the other hand would be stored in a separate table, to allow for flexible manipulation(summing). There are one more tricky design. If I have multiple chicken, how do I know which chicken to cook when I use a recipe to cook directly? I design the system to prioritize in cooking the one that have the least days_until_expired.

**tools.py** - This python file keeps the self-define functions I can use in the app.py file.

The main difference between my final project and pset 9 is that I add many jQuery code to allow more user interaction with the current web page. For example a extendable list, a AJAX call on ingredient when click the recipe name, or enable/disable buttons when the conditions are met.
### Languages
python/ HTML/ css/ JavaScript/ jQuery/ SQL
### Plug-ins
[DataTable](https://www.datatables.net/)/ [Bootstrap](https://getbootstrap.com/)
