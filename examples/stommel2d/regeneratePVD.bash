#!/bin/bash

end=320
OUT=$1
python generatePVD.py -d $OUT -e $end -n Elevation2d
python generatePVD.py -d $OUT -e $end -n Velocity2d
