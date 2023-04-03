# Realtime display of Large Scale 

## Summary 

The LPT data update once a day on crontab. Real-time tracking is for the 90 days ending with *yesterday*.

A time-longitude plot of rainfall and LPT system (LPTs) centroid is on the left, and on the right a map plot of LPT system centroid. It can be selected whether all LPTs are displayed, or just MJO LPTs. Both of these plots are interactive, using Plotly Dash.

Further interactivity is provided by the time range drop-down menu, which shows the recent 90-day tracking results as well as the previous years' annual tracking results.


## Deploying

I had to go through a bit of "trickery" to deploy this on orca!
I'm using WSGI and Apache here.

The steps were:
- Clone this repo to /var/www/FLASKAPPS/lpt
- Run the script do.build_python_environment.sh.
    - This install some stuff
    - but eventually throws an error about Pillow and zlib not being found.
- Downgrade the version of PIP.
    - `source ./venv/bin/activate` to activate the virtual environment.
    - `python -m pip install pip==19.3.1`
    - (I figured this out from https://github.com/python-pillow/Pillow/issues/4242)
- `pip3 install -r requirements.txt` to manually install the rest of requirements.txt
- Set up a cache directory for Numba.
    - Comment out these lines in app.wsgi:

```
if whoami == 'www-data':
    os.environ['NUMBA_CACHE_DIR']='/var/www/FLASKAPPS/lpt/numba_cache'
else:
    os.environ['NUMBA_CACHE_DIR']='/var/www/FLASKAPPS/lpt/numba_cache_testing'
```

    - `mkdir /var/www/FLASKAPPS/lpt/numba_cache`
    - `sudo chown www-data /var/www/FLASKAPPS/lpt/numba_cache`
- Re-start Apache: `sudo /etc/init.d/apache2 reload`
