## Lets find the smoking gun:
    - Lets look at how the overdose and usage rate of illegal drugs vs prescription drug deaths over time
    - We could try to find a link to the overdose rate being connected to the increase of death with illegal drugs.
    - Also finding how the drug ovedose death rates spread throughout the United states over time, seeing where the death rates starting spiking and showing how it spread throughout the United states, which could even test if the drugs are really coming in from the south across the border or if tey are comming from all around.
    - We could also link this to major cities to see how the drugs spread through the US 
    - Are new_rx a subset of total_rx?
    - Do new_rx represent a greater quantity of medicaid?  it seems that new_rx is a lower proportion of non-medicaid (long term use?)

  ## Bullet Factors:
    - Border Seizures
    - Methadone clinics (open for business)
    - Rehab industry revenue
    - Illicit opioid arrests
    - Deaths from illicit

## Is the prescription / overdose phenomenon
    - income by zip code
    - medicaid proportion by zip code

## Locations:
    - Big Cities
    - Indiana (county)
    - North Carolina/Tennessee ()

## Next Thing To Do (Executable)

1. Get CDC WONDER by drug type (State × Year × Drug/Alcohol Induced Cause)
    - Save as: `Datasets/Multiple Cause of Death, Drug Type, 1999-2020.csv`
    - This enables heroin/fentanyl/cocaine/psychostimulant tracking over time.

2. Build CDC drug-type outputs + merge with IQVIA state-year panel
    - Run: `python main.py q6`
    - Run: `python main.py cdc-drug`
    - Output panel: `output/cdc/iqvia_cdc_state_year_illicit_panel.csv`

3. Build time-based US geo spread map for illicit overdose deaths
    - Run: `python main.py map-illicit`
    - Output map: `output/cdc/illicit_overdose_spread_map.html`

4. Use this panel to test your core hypothesis
    - Compare trend breaks after ~2012 by state.
    - Check whether illicit-overdose rates rise while Rx volume declines.
    - Identify first spike states and possible diffusion pattern to nearby states/regions.

# KEY NEW THINGS TO DO
- From 2008-2017: every county in the US:
  - total prescriptions, new prescriptions, average MME
  - number of prescriptions on medicaid vs non medicaid
  - overdose deaths
  


# CDC PREDICTION DATA TO PULL
- Want to do time series analysis on drug overdose death rate by county 
- want group by county (residence first), and then occurence for time series analysis
- 