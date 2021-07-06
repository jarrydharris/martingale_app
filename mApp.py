import dash
import flask
import dash_core_components as dcc
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from random import choices
from pandas import DataFrame
import plotly.graph_objs as go


def spin(pr):
    """Simulates the outcome of betting red or black on a roulette wheel

    Parameters:
    pr (tuple): Probability distribution for red, black or neither(green)

    Returns:
    string: red, black, green

    """
    return choices(["red", "black", "green"], weights=(pr[0], pr[1], pr[2]))[0]


def next_bet(current, strategy):
    """Returns the next bet based on the current bet and betting strategy.
    Standard increases by AUD denominations until reaching 100. Non standard
    betting strategy doubles each time

    Parameters:
    current (int): The current bet to be increased for the next roll
    strategy (string): 'standard' or 'exponential' which formula to use
    to determine next bet

    Returns
    int: The value of the next bet.
    """
    if strategy == 'standard':
        if current is None:
            return 5
        elif current == 5:
            return 10
        elif current == 10:
            return 20
        elif current == 20:
            return 50
        else:
            return 100
    else:
        if current is None:
            return 5
        else:
            return 2*current


def mart(color, wallet, walkout, spins, bet, wheel):
    """Simulates a session of roulette with a starting amount of money (wallet),
    a value in which the player will take their profit and leave (wallet),
    number of spins (spin), betting strategy (bet), probability distribution
    follows an american, european or other style (wheel)

    Parameters:
    color (string): 'black' or 'red', the color that is win for each roll
    wallet (int): starting balance
    walkout (int): if balance exceeds this value you stop betting and keep
    profit
    spins (int): number of spins until you stop playing
    bet (string): 'standard' or 'exponential', standard bets 5, 10, 20, 50,
    100 dollars, exponential doubles bet 2^x
    wheel (string): 'american', 'european', 'even', probability of winning,
    american wheel has 18 red, 18 black and 2 green, european has 18 red,
    18 black and 1 green, even is with no house odds (no green).


    Returns:
    pandas.core.frame.DataFrame: pandas data frame containing the outcome of
    the sessions
    """

    starting_wallet = wallet
    number_of_spins = 0
    current_bet = next_bet(None, bet)

    if wheel == 'american':
        pr = (18/38, 18/38, 2/38)
    elif wheel == 'european':
        pr = (18/37, 18/37, 1/37)
    else:
        pr = (1/2, 1/2, 0)

    data = {'spin': [], 'profit': []}

    while ((wallet - current_bet > 0 and wallet <= walkout) and
            number_of_spins < spins):
        # Player has enough money to bet and still hasn't won their target
        # profit so we can continue betting

        wallet = wallet - current_bet
        number_of_spins += 1
        if spin(pr) == color:
            wallet += 2*current_bet
            current_bet = next_bet(None, bet)
        else:
            current_bet = next_bet(current_bet, bet)

        data['spin'].append(number_of_spins)
        data['profit'].append(wallet - starting_wallet)

    return data


def doubleMart(wallet, walkout, spins, bet, wheel):
    """The same as mart() however the player bets an equal share on black and
    red Simulates multiple sessions of roulette with a starting amount of money
    (wallet), a value in which the player will take their profit and leave
    (wallet), number of spins (spin), betting strategy (bet), probability
    distribution follows an american, european or other style (wheel)

    Parameters:
    color (string): 'black' or 'red', the color that is win for each roll
    wallet (int): starting balance
    walkout (int): if balance exceeds this value you stop betting and keep
    profit
    spins (int): number of spins until you stop playing
    bet (string): 'standard' or 'exponential', standard bets 5, 10, 20, 50,
    100 dollars, exponential doubles bet with no cap
    wheel (string): 'american', 'european', 'even', probability of winning,
    american wheel has 18 red, 18 black and 2 green, european has 18 red,
    18 black and 1 green, even is with no house odds (no green).


    Returns:
    dictionary: containing the outcome of the session
    """

    starting_wallet = wallet
    number_of_spins = 0
    b_current_bet = next_bet(None, bet)
    r_current_bet = next_bet(None, bet)

    if wheel == 'american':
        pr = (18/38, 18/38, 2/38)
    elif wheel == 'european':
        pr = (18/37, 18/37, 1/37)
    else:
        pr = (1/2, 1/2, 0)

    data = {'spin': [], 'profit': []}

    while ((wallet - (b_current_bet + r_current_bet) > 0 and
            wallet <= walkout) and number_of_spins < spins):
        # Player has enough money to bet and still hasn't won their target
        # profit so we can continue betting

        wallet = wallet - (b_current_bet + r_current_bet)
        number_of_spins += 1
        if spin(pr) == 'black':
            wallet += 2*b_current_bet
            b_current_bet = next_bet(None, bet)
            r_current_bet = next_bet(r_current_bet, bet)
        else:
            wallet += 2*r_current_bet
            r_current_bet = next_bet(None, bet)
            b_current_bet = next_bet(b_current_bet, bet)

        data['spin'].append(number_of_spins)
        data['profit'].append(wallet - starting_wallet)

    return data


def run(n, color, wallet, walkout, spins, bet, wheel):
    """Completes n martingale runs

    Parameters:
    n (int): number of runs upper bound

    Returns:
    pandas.core.frame.DataFrame: contains outcomes of n sessions
    """

    d = {}
    for i in range(0, n):
        d[str(i)] = mart(color, wallet, walkout, spins, bet, wheel)

    d = DataFrame(d)
    d = d.transpose()
    return d


def max_length(df):
    """Helper function for profit_filler, interates through the results of spins
    and returns the longest set of spins.

    Parameters:
    df (pandas.core.frame.DataFrame): data frame containing the simulation
    results

    Returns:
    int: The maximum length of the spin counts

    """
    row_lengths = list(map(lambda x: len(x), df['spin']))
    return max(row_lengths)


def profit_filler(df, max_length):
    """Takes a dataframe and ensures all the profit rows are the same length for
    adding together profits over the number of games, shorter rows will be
    filled with their final value.
    example: row 0 = [1,2,3,4], row 1 = [1,2,3] -> row 0 = [1,2,3,4],
    row 1 = [1,2,3,3]

    Parameters:
    df (pandas.core.frame.DataFrame): data frame containing the simulation
    results
    max_length (int): The longest set of results in the simulation

    Returns:
    pandas.core.frame.DataFrame: The simulation results converted to be used
    for calculating profit. All runs being the same length with the shorter
    rows maintaining its final value.
    """
    spin = [i for i in range(1, max_length + 1)]
    data = df
    for i in range(len(data['profit'])):
        size = max_length - len(data['profit'][i])
        data['profit'][i].extend([data['profit'][i][-1]]*size)
        data['spin'][i] = spin

    return data


def sum_runs(df):
    """Adds together all the runs to get a value for total profit

    Parameters:
    df (pandas.core.frame.DataFrame): data frame containing the simulation

    Returns:
    dictionary: dictionary containing the results summed up for the total
    profit visualisation.
    """
    lists = [i for i in df['profit']]
    total_profit = list(map(sum, zip(*lists)))
    data = {'spin': df['spin'][0], 'profit': total_profit}
    return data

# Text for the page instructions
instructions = '''

# Instructions:

This is a simulation of outcomes for betting on roulette with a [martingale st\
rategy](https://en.wikipedia.org/wiki/Martingale_(betting_system)).
Change the inputs and then click the "Run Simulation" button to see the result\
s.
Each game will run until the player reaches the max number of spins (average n\
umber of spins a single player completes in an hour is 112).
The player increases their bet each loss and resets on a win. If the players n\
ext bet exceeds their current funds or reaches the walkout threashold
they stop playing and leave with their current balance.

## Inputs:

- **Number of games:** This is the number of times a player enters a casio and\
sits down for a roulette session (min = 2, max = 1000).
- **Color:** The color to bet on (Black or red).
- **Starting wallet size:** How much money the player begins with (min = 10, m\
ax = 1000000).
- **Walkout:** The threshold for which a player takes their money and stops th\
e session (min = Starting wallet size + 5, max = 2000000).
- **Number of spins:** The number of spins the player stays at the table befor\
e leaving (min = 2, max = 1000).
- **Betting method:** Standard involves going up a denomination in Australian \
currency until maxing out at which it will stay at $100 until a win. Exponenti\
al will double each loss. (Standard or Exponental).
- **Wheel type:** The type of roulette wheel played on. American has the worst\
odds for the player, European is slightly better, Even is just a 50/50 chance \
for comparison. (American, European, Even)

## Outputs:

- **Left Graph:** Shows the profit (starting amount - current balance at spin \
x) for each individual game.
- **Right Graph:** Shows the total profit if you add each run together.

'''

external_stylesheets = [dbc.themes.SANDSTONE]

server = flask.Flask(__name__)

app = dash.Dash(
        __name__,
        server=server,
        external_stylesheets=external_stylesheets
    )

app.layout = dbc.Container(
    children=[
        dbc.Row(  # Graphs
            [
                dbc.Col(dcc.Graph(id="runs_graph"), align='centre'),
                dbc.Col(dcc.Graph(id='total_graph'), align='centre')
            ], justify='centre'),
        dbc.Row([
            dbc.Button("Run Simulation", id="run", n_clicks=0, size='lg')
        ], align='centre', justify='centre'),
        dbc.Row([  # inputs
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Number of games: "),
                    dbc.Input(
                            id="n",
                            placeholder="Enter number of games...",
                            type="number",
                            value=10,
                            min=1,
                            max=1000
                        )
                ]
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Color: "),
                    dbc.Select(id="color", options=[
                        {"label": "Black", "value": "black"},
                        {"label": "Red", "value": "red"}
                        ], value="black")
                ]
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Starting wallet size: "),
                    dbc.Input(
                        id="wallet",
                        placeholder="Enter a dollar value to start playing \
                            with...",
                        type="number", value=1000, min=5, max=1000000)
                ]
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Walkout: "),
                    dbc.Input(
                        id="walkout",
                        placeholder="Enter a value to take winnings...",
                        type="number", value=2000, min=5, max=2000000)
                ]
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Number of spins: "),
                    dbc.Input(
                        id="spins",
                        placeholder="Enter the number of spins \
                        the player stays for...", type="number",
                        value=112, min=1, max=1000)
                ]
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Betting method: "),
                    dbc.Select(id="bet", options=[
                        {"label": "Standard ($5, $10, $20, $50, $100)",
                            "value": "standard"},
                        {"label": "Exponential ($5, $10, $20, $40, $80, $160, \
                            ...)",
                            "value": "exponential"}
                        ], value='standard')
                ]
            ),
            dbc.InputGroup(
                [
                    dbc.InputGroupAddon("Wheel type: "),
                    dbc.Select(id="wheel", options=[
                        {"label": "American (18 reds, 18 blacks, 2 greens)",
                            "value": "american"},
                        {"label": "European (18 reds, 18 blacks, 1 green)",
                            "value": "european"},
                        {"label": "Even (18 reds, 18 blacks, no green)",
                            "value": "even"}
                        ], value='american')
                ]
            )
        ]),
        dcc.Markdown(children=instructions)

    ]
    )


@app.callback(
    [
        Output("runs_graph", "figure"),
        Output("total_graph", "figure")
    ],
    [Input("run", "n_clicks")],
    [
        State("n", "value"),
        State("color", "value"),
        State("wallet", "value"),
        State("walkout", "value"),
        State("spins", "value"),
        State("bet", "value"),
        State("wheel", "value")
    ]
)
def update_output(
        n_clicks=0, n=10, color='black', wallet=1000, walkout=2000,
        spins=100, bet='standard', wheel='american'):
    if n < 1:
        n = 2
    if wallet < 10:
        wallet = 10
    if walkout < (wallet + 5):
        walkout = wallet + 5
    if spins < 1:
        spins = 1

    data = run(n, color, wallet, walkout, spins, bet, wheel)
    ml = max_length(data)
    standardized = profit_filler(data, ml)
    total = sum_runs(standardized)

    break_even = go.Line(
                    y=[0]*len(total['profit']),
                    line_dash='dash',
                    name='Break even',
                    line=dict(color='black')
                )

    fig = go.Figure(
        data=[
            {'y': data['profit'][str(i)],
                'type':'scatter',
                'name': 'Game ' + str(i+1)} for i in range(len(data['profit']))
            ],
        layout={
            'title': 'Individual Games: ',
            'xaxis': {'title': 'Spin'},
            'yaxis': {'title': 'Profit'}
        }
    )

    fig.add_trace(break_even)

    fig.update_layout(
        title_text="Profit of individual games:",
        xaxis_title="Spin",
        yaxis_title="Profit ($)"
    )

    fig2 = go.Figure()

    fig2.add_trace(break_even)

    fig2.add_trace(
        go.Line(
            y=total['profit'],
            name='Total profit',
            line=dict(color='black')
        )
    )

    rg = ['rgb(255,0,0)' if x < 0 else 'rgb(0,255,0)' for x in total['profit']]
    fig2.add_trace(
        go.Scatter(
            y=total['profit'],
            name='Profit/Loss',
            mode='markers',
            marker=dict(color=rg, size=[5]*len(total['profit']))
        )
    )

    fig2.update_layout(
        title_text="Total profit of all games:",
        xaxis_title="Spin",
        yaxis_title="Profit ($)"
    )

    return fig, fig2


@app.callback(
    Output("walkout", "min"),
    [Input("wallet", "value")]
)
def min_walkout(value):
    if value is None:
        value = 10
    elif value < 10:
        value = 10
    return value + 5
