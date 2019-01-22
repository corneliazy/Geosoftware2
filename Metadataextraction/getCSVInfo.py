import click,json, sqlite3, pygeoj, csv
from osgeo import gdal, ogr, osr
import pandas as pd
import numpy as np
import extractTool
from scipy.spatial import ConvexHull
import dateparser
from pyproj import Proj, transform
#import sys

#import ogr2ogr
#ogr2ogr.BASEPATH = "/home/caro/Vorlagen/Geosoftware2/Metadatenextraktion"

"""
Function for extracting the bounding box of a csv file
@see https://www.programiz.com/python-programming/reading-csv-files

:param filepath: path to the file
:param detail: specifies the level of detail of the geospatial extent (bbox or convex hull)
:param folder: specifies if the user gets the metadata for the whole folder (whole) or for each file (single)
:param time: boolean variable, if it is true the user gets the temporal extent instead of the spatial extent
:returns: spatial extent as a bbox in the format [minlon, minlat, maxlon, maxlat]
"""

def getCSVbbx(filepath, detail, folder, time):
    #format validation
    pd.read_csv(filepath)
    click.echo("csv")
    CRSinfo = True
    listlat = ["Koordinate_Hochwert","lat","Latitude","latitude"]
    listlon = ["Koordinate_Rechtswert","lon","Longitude","longitude","lng"]
    listCRS = ["CRS","crs","Koordinatensystem","EPSG","Coordinate reference system", "coordinate system"]
    listtime = ["time", "timestamp", "date", "Time", "Jahr", "Datum"]

    try:
        deli=';'
        df = pd.read_csv(filepath, delimiter=deli,engine='python')
        click.echo("hi;")

    except Exception as exce:
        deli=','
        df = pd.read_csv(filepath, delimiter=deli,engine='python')
        click.echo("hi,")
 
    #tests if there is a column named coordinate reference system or similar       
    if not intersect(listCRS,df.columns.values):
        CRSinfo= False
        print("hu")
        print("No fitting header for a reference system")
    else:
        CRSinfo= True
        my_crs_identifier=intersect(listCRS,df.columns.values)
        my_crs_code=df[my_crs_identifier[0]]
        # save the first one
        my_crs_code_1=my_crs_code[0]
            

    # check if there are columns for latitude, longitude and timestamp
    if not(intersect(listlat,df.columns.values) and intersect(listlon,df.columns.values)):
        raise Exception('No fitting header for latitudes,longitudes')
    else:
        my_lat=intersect(listlat,df.columns.values)
        my_lon=intersect(listlon,df.columns.values)

    if intersect(listtime,df.columns.values):
        my_time_identifier=intersect(listtime,df.columns.values)
    else:
        click.echo("No time information available")

    # saves the coordinate values for latitude and longitude
    lats=df[my_lat[0]]
    lons=df[my_lon[0]]
    
    if detail =='bbox':
        click.echo("bbox23")
        # Using Pandas: http://pandas.pydata.org/pandas-docs/stable/io.html
        bbox=[min(lats),min(lons),max(lats),max(lons)]
        # CRS transformation if there is information about crs
        if(CRSinfo):
            # my_crs_code includes the list of the identifiers of the CRS
            lat1t,lng1t = extractTool.transformToWGS84(min(lats),min(lons), my_crs_code_1)
            lat2t,lng2t = extractTool.transformToWGS84(max(lats),max(lons), my_crs_code_1)
            bbox=[lat1t,lng1t,lat2t,lng2t]
            if folder=='single':
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("Boundingbox of the CSV object:")
                click.echo(bbox)
                print("----------------------------------------------------------------")
                extractTool.ret_value.append(bbox)
            if folder=='whole':
                extractTool.bboxArray.append(bbox)
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("Boundingbox of the CSV:")
                click.echo(bbox)
                print("----------------------------------------------------------------")
        else:
            if folder=='single':
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("Boundingbox of the CSV object:")
                print(bbox)
                print("Missing CRS -----> Boundingbox will not be saved in zenodo.")
                print("----------------------------------------------------------------")
                extractTool.ret_value.append([None])
            if folder=='whole':
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("Boundingbox of the CSV file:")
                click.echo(bbox)
                click.echo("because of a missing crs this CSV is not part of the folder calculation.")
                print("----------------------------------------------------------------")

    else:
        extractTool.ret_value.append([None])

    #returns the convex hull of the coordinates from the CSV object.
    if detail == 'convexHull':
        click.echo("convexHull")
        coords=np.column_stack((lats, lons))
        #definition and calculation of the convex hull
        hull=ConvexHull(coords)
        hull_points=hull.vertices
        convHull=[]
        for z in hull_points:
            point=[coords[z][0], coords[z][1]]
            convHull.append(point)
        if(CRSinfo):
            for z in coords:
                z[0],z[1] = extractTool.transformToWGS84(z[0],z[1], my_crs_code_1)
            if folder=='single':
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("convex Hull of the csv file: ")
                click.echo(convHull)
                print("----------------------------------------------------------------")
                extractTool.ret_value.append(convHull)
            if folder=='whole':
                extractTool.bboxArray=extractTool.bboxArray+convHull
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("convex hull of the CSV:")
                click.echo(convHull)
                print("----------------------------------------------------------------")
                #return convHull
        else:
            if folder=='single':
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("Convex hull of the CSV object:")
                print(convHull)
                print("Missing CRS -----> Boundingbox will not be saved in zenodo.")
                print("----------------------------------------------------------------")
                extractTool.ret_value.append([None])
            if folder=='whole':
                print("----------------------------------------------------------------")
                click.echo("Filepath:")
                click.echo(filepath)
                click.echo("Convex hull of the CSV file:")
                click.echo(convHull)
                click.echo("because of a missing crs this CSV is not part of the folder calculation.")
                print("----------------------------------------------------------------")

    else:
        extractTool.ret_value.append([None])
    
    if (time):
        click.echo("hallo")
        # Using Pandas: http://pandas.pydata.org/pandas-docs/stable/io.html
        df = pd.read_csv(filepath, sep=';|,',engine='python')
        click.echo(my_time_identifier)
        if not my_time_identifier:
            print("No fitting header for time-values")
            extractTool.ret_value.append([None])
        else:
            time=df[my_time_identifier[0]]
            print(min(time))
            print(max(time))
            timemin=str(min(time))
            timemax=str(max(time))
            timemax_formatted=dateparser.parse(timemax)
            timemin_formatted=dateparser.parse(timemin)
            timeextend=[timemin_formatted, timemax_formatted]
            print(timeextend)
            if folder=='single':
                print("----------------------------------------------------------------")
                click.echo("Timeextend of this CSV file:")
                click.echo(timeextend)
                print("----------------------------------------------------------------")
                extractTool.ret_value.append([timeextend])
                #return timeextend
            if folder=='whole':
                extractTool.timeextendArray.append(timeextend)
                print("timeextendArray:")
                print(extractTool.timeextendArray)

    else:
        extractTool.ret_value.append([None])
    if folder=='single':
        print(extractTool.ret_value)
        return extractTool.ret_value

"""
Auxiliary function for testing if an identifier for the temporal or spatial extent is part of the header in the csv file
:param a: collection of identifiers
:param b: collection of identifiers
:returns: equal identifiers
"""
def intersect(a, b):
     return list(set(a) & set(b))
