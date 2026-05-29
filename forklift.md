# Forklift notes

Use gcloud console to create a tunnel to the gce vm, then any RDP

- gcloud auth login (opens browser)
- gcloud compute start-iap-tunnel <server name> 3389 (port #) --project <gcp-project-name>
- use local RDP client to login w/service account in bitwarden
  - .\127.0.0.1:<port>
  - I had to have the . in front of the slash to get it to work on forklift, but not web api

double check broadband cloud vs forklift vm
Every lift it clears out all the data from the previous lift, so if 

hashed: all the data that forklift is interested in knowing if it is changed
    doesn't get deleted unless scorched earth
    Anything that participates in a crate gets copied to here
receiving
    Where the lift stages data
    file gdbs that the last lift produces for the ship to copy to arcgis server folder
    contents get deleted on every lift
    packing slip:
        everything forklift needs to do
        pallets that don't put data in staging may still have steps defined in here
        if the packing slip was empty, the ship would still move the gdbs to the agrcgis server folder
    if the ship fails and lift hasn't re-run, you can re-run the ship to try again

## troubleshooting
DEQ- probably leave for scott, dont' worry about append errors
error in acccessing describe- source data were unavailable
    error in lift means nothing will be changed this round, let it go another run to see if its a real problem
Dolly errors
    probably let them go, Dolly does its own change detection and stores in firestore, so if an update doesn't work it'll probably see the change the next round and run
Dolly hanging on append
    if there's lift but not ship- log in and check logs, it would be apparent if it's hung on append
    kill the forklift process, manually kick off forklift ship (`forklift ship`)
    ship does shut down the arcgis server service while moving
        vista and old spills rely on that
    dolly is in the forklift env

## web API machine
api runs as cloud run services which pass requests to arcgis server on the VM
first tab in edge, calanus user
Geolocators
    main geolocator services
    When forklift sees new road/addr point data, it creates new locators, shares them to a bucket, on VM a scheduled task pulls the locators down 
    script in e:\github\api.mapserve.utah.gov\pforklift\locatorupdate.py
troubleshooting: usually just restart the locators
e:\data\Production
