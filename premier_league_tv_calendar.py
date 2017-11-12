from selenium import webdriver
from time import sleep

#Dep: needs to be installed
driver = webdriver.Chrome('/usr/local/bin/chromedriver')
driver.set_window_size(1120, 550)

driver.get('https://www.premierleague.com/broadcast-schedules')

#Scrolling to the bottom of the page makes the rest of the games load
driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")


initial_displayed_fixtures = len(driver.find_elements_by_css_selector('li.matchFixtureContainer'))

#Wait until the games are loaded in asynchronously
current_displayed = initial_displayed_fixtures
while(current_displayed <= initial_displayed_fixtures):
    sleep(1)
    current_displayed = len(driver.find_elements_by_css_selector('li.matchFixtureContainer'))
    print 'Waiting for games to load...'


games = []
matchdays = driver.find_elements_by_css_selector('time.date.long')
game_day_fixtures = driver.find_elements_by_css_selector('time.date.long ~ ul.matchList')

print '{} game days found'.format(len(game_day_fixtures))
for index, value in enumerate(matchdays):
    matchday_date = matchdays[index].get_attribute('datetime')
    games_on_day = game_day_fixtures[index].find_elements_by_css_selector('li.matchFixtureContainer')

    for gameElem in games_on_day:
        gameDetails = {}

        teamsElems = gameElem.find_elements_by_css_selector('span.teamName')
        teams = {}
        teams['home'] = teamsElems[0].get_property('innerText')
        teams['away'] = teamsElems[1].get_property('innerText')
        time = gameElem.find_element_by_css_selector('time').get_property('innerText')
        broadcasterElem = gameElem.find_element_by_css_selector('span.broadcaster > span')
        if ('SKY' in broadcasterElem.get_attribute('class')):
            broadcaster = 'SKY Sports'
        elif ('BT' in broadcasterElem.get_attribute('class')):
            broadcaster = 'BT Sport'
        else:
            raise ValueError('expected broadcaster to be BT or SKY')
        gameDetails['teams'] = teams
        gameDetails['time'] = time
        gameDetails['broadcaster'] = broadcaster 
        gameDetails['date'] = matchday_date
        games.append(gameDetails)

    
for game in games:
    print game

driver.close()


