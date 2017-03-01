from __future__ import division # allows floating point division from integers
import FreeCAD, Part, math
import os, dummy, FreeCADGui
from FreeCAD import Base
from pivy import coin

path_curvesWB = os.path.dirname(dummy.__file__)
path_curvesWB_icons =  os.path.join( path_curvesWB, 'Resources', 'icons')

# ********************************************************
# **** Part.BSplineCurve.interpolate() documentation *****
# ********************************************************

#Replaces this B-Spline curve by approximating a set of points.
#The function accepts keywords as arguments.

#approximate2(Points = list_of_points) 

#Optional arguments :

#DegMin = integer (3) : Minimum degree of the curve.
#DegMax = integer (8) : Maximum degree of the curve.
#Tolerance = float (1e-3) : approximating tolerance.
#Continuity = string ('C2') : Desired continuity of the curve.
#Possible values : 'C0','G1','C1','G2','C2','C3','CN'

#LengthWeight = float, CurvatureWeight = float, TorsionWeight = float
#If one of these arguments is not null, the functions approximates the 
#points using variational smoothing algorithm, which tries to minimize 
#additional criterium: 
#LengthWeight*CurveLength + CurvatureWeight*Curvature + TorsionWeight*Torsion
#Continuity must be C0, C1 or C2, else defaults to C2.

#Parameters = list of floats : knot sequence of the approximated points.
#This argument is only used if the weights above are all null.

#ParamType = string ('Uniform','Centripetal' or 'ChordLength')
#Parameterization type. Only used if weights and Parameters above aren't specified.

#Note : Continuity of the spline defaults to C2. However, it may not be applied if 
#it conflicts with other parameters ( especially DegMax ).    parametrization


DEBUG = 0

def debug(string):
    if DEBUG:
        FreeCAD.Console.PrintMessage(string)
        FreeCAD.Console.PrintMessage("\n")


class Approximate:
    def __init__(self, obj , source):
        ''' Add the properties '''
        debug("\nApproximate class Init\n")
        obj.addProperty("App::PropertyLink",         "PointObject",  "Approximate", "Object containing the points to approximate").PointObject = source
        obj.addProperty("App::PropertyInteger",      "DegreeMin",    "General",     "Minimum degree of the curve").DegreeMin = 3
        obj.addProperty("App::PropertyInteger",      "DegreeMax",    "General",     "Maximum degree of the curve").DegreeMax = 8
        obj.addProperty("App::PropertyFloat",        "ApproxTolerance",    "General",     "Approximation tolerance").ApproxTolerance = 0.05
        obj.addProperty("App::PropertyEnumeration",  "Continuity",   "General",     "Desired continuity of the curve").Continuity=["C0","C1","G1","C2","G2","C3","CN"]
        obj.addProperty("App::PropertyEnumeration",  "Method",       "General",     "Approximation method").Method=["Parametrization","Smoothing Algorithm"]
        obj.addProperty("App::PropertyEnumeration",  "Parametrization", "Parameters", "Parametrization type").Parametrization=["ChordLength","Centripetal","Uniform"]
        obj.addProperty("App::PropertyFloatConstraint",        "LengthWeight",    "Parameters",       "Weight of curve length for smoothing algorithm").LengthWeight=1.0
        obj.addProperty("App::PropertyFloatConstraint",        "CurvatureWeight", "Parameters",       "Weight of curve curvature for smoothing algorithm").CurvatureWeight=1.0
        obj.addProperty("App::PropertyFloatConstraint",        "TorsionWeight",   "Parameters",       "Weight of curve torsion for smoothing algorithm").TorsionWeight=1.0
        obj.addProperty("App::PropertyInteger",      "FirstIndex",    "Range",   "Index of first point").FirstIndex = 0
        obj.addProperty("App::PropertyInteger",      "LastIndex",     "Range",   "Index of last point").LastIndex = 10
        #obj.addProperty("App::PropertyVectorList",   "Points",    "Approximate",   "Points")
        obj.addProperty("Part::PropertyPartShape",   "Shape",     "Approximate",   "Shape")
        obj.Proxy = self
        self.Points = []
        obj.LengthWeight =    (1.0,0.01,10.0,0.1)
        obj.CurvatureWeight = (1.0,0.01,10.0,0.1)
        obj.TorsionWeight =   (1.0,0.01,10.0,0.1)
        obj.Method = "Parametrization"
        obj.Parametrization = "ChordLength"
        obj.Continuity = 'C2'
        self.getPoints(obj)
        #obj.FirstIndex = 0
        obj.LastIndex = len(self.Points)-1
        self.execute(obj)

        
    #def selectedEdgesToProperty(self, obj, edge):
        #objs = []
        #for o in edge:
            #if isinstance(o,tuple) or isinstance(o,list):
                #if o[0].Name != obj.Name:
                    #objs.append(tuple(o))
            #else:
                #for el in o.SubElementNames:
                    #if "Edge" in el:
                        #if o.Object.Name != obj.Name:
                            #objs.append((o.Object,el))
        #if objs:
            #obj.Edge = objs
            #debug(str(edge) + "\n")
            #debug(str(obj.Edge) + "\n")


    def getPoints( self, obj):
        try:
            self.Points = obj.PointObject.Points
        except:
            self.Points = [v.Point for v in obj.PointObject.Shape.Vertexes]

    def buildCurve(self, obj):
        pts = self.Points[obj.FirstIndex:obj.LastIndex+1]
        bs = Part.BSplineCurve()
        if obj.Method == "Parametrization":
            bs.approximate(Points = pts, DegMin = obj.DegreeMin, DegMax = obj.DegreeMax, Tolerance = obj.ApproxTolerance, Continuity = obj.Continuity, ParamType = obj.Parametrization)
        elif obj.Method == "Smoothing Algorithm":
            bs.approximate(Points = pts, DegMin = obj.DegreeMin, DegMax = obj.DegreeMax, Tolerance = obj.ApproxTolerance, Continuity = obj.Continuity, LengthWeight = obj.LengthWeight, CurvatureWeight = obj.CurvatureWeight , TorsionWeight = obj.TorsionWeight)
        self.curve = bs

    def execute(self, obj):
        debug("\n* Approximate : execute *\n")
        self.getPoints( obj)
        self.buildCurve( obj)
        obj.Shape = self.curve.toShape()

    def onChanged(self, fp, prop):
        #print fp
        if not fp.PointObject:
            return
        if prop == "PointObject":
            debug("Approximate : PointObject changed\n")
            self.getPoints( fp)
            fp.FirstIndex = 0
            fp.LastIndex = len(self.Points)-1
                
        if prop == "Method":
            debug("Approximate : Method changed\n")
            if fp.Method == "Parametrization":
                fp.setEditorMode("Parametrization", 0)
                fp.setEditorMode("LengthWeight", 2)
                fp.setEditorMode("CurvatureWeight", 2)
                fp.setEditorMode("TorsionWeight", 2)
            elif fp.Method == "Smoothing Algorithm":
                fp.setEditorMode("Parametrization", 2)
                fp.setEditorMode("LengthWeight", 0)
                fp.setEditorMode("CurvatureWeight", 0)
                fp.setEditorMode("TorsionWeight", 0)
                if fp.Continuity in ["C3","CN"]:
                    fp.Continuity = 'C2'
                    
        if prop == "Continuity":
            if fp.Method == "Smoothing Algorithm":
                if fp.Continuity == 'C1':
                    if fp.DegreeMax < 3:
                        fp.DegreeMax = 3
                elif fp.Continuity in ['G1','G2','C2']:
                    if fp.DegreeMax < 5:
                        fp.DegreeMax = 5
            debug("Approximate : Continuity changed to "+str(fp.Continuity))

        if prop == "DegreeMin":
            if fp.DegreeMin < 2:
                fp.DegreeMin = 2
            elif fp.DegreeMin > fp.DegreeMax:
                fp.DegreeMin = fp.DegreeMax
            #fp.DegreeMax = fp.DegreeMax
            debug("Approximate : DegreeMin changed to "+str(fp.DegreeMin))
        if prop == "DegreeMax":
            if fp.DegreeMax < fp.DegreeMin:
                fp.DegreeMax = fp.DegreeMin
            elif fp.DegreeMax > 14:
                fp.DegreeMax = 14
            if fp.Method == "Smoothing Algorithm":
                if fp.Continuity in ['G1','G2','C2']:
                    if fp.DegreeMax < 5:
                        fp.DegreeMax = 5
                elif fp.Continuity == "C1":
                    if fp.DegreeMax < 3:
                        fp.DegreeMax = 3
                #fp.DegreeMin = fp.DegreeMin
            debug("Approximate : DegreeMax changed to "+str(fp.DegreeMax))
        if prop == "ApproxTolerance":
            if fp.ApproxTolerance < 1e-6:
                fp.ApproxTolerance = 1e-6
            elif fp.ApproxTolerance > 1000.0:
                fp.ApproxTolerance = 1000.0
            debug("Approximate : ApproxTolerance changed to "+str(fp.ApproxTolerance))

        if prop == "FirstIndex":
            if fp.FirstIndex < 0:
                fp.FirstIndex = 0
            elif fp.FirstIndex > fp.LastIndex-1:
                fp.FirstIndex = fp.LastIndex-1
            debug("Approximate : FirstIndex changed to "+str(fp.FirstIndex))
        if prop == "LastIndex":
            if fp.LastIndex < fp.FirstIndex+1:
                fp.LastIndex = fp.FirstIndex+1
            elif fp.LastIndex > len(self.Points)-1:
                fp.LastIndex = len(self.Points)-1
            debug("Approximate : LastIndex changed to "+str(fp.LastIndex))

            
    def __getstate__(self):
        return None

    def __setstate__(self,state):
        return None


class approx:
    def parseSel(self, selectionObject):
        res = []
        for obj in selectionObject:
            if len(obj.Object.Shape.Vertexes) > 1:
                return obj.Object
        FreeCAD.Console.PrintMessage("\nPlease select an object that has at least 2 vertexes")
        return None

    def Activated(self):
        s = FreeCADGui.Selection.getSelectionEx()
        source = self.parseSel(s)
        if not source:
            return False
        obj=FreeCAD.ActiveDocument.addObject("Part::FeaturePython","Approximation_Curve") #add object to document
        Approximate(obj,source)
        obj.ViewObject.Proxy = 0
        FreeCAD.ActiveDocument.recompute()
            
    def GetResources(self):
        return {'Pixmap' : path_curvesWB_icons+'/approximate.svg', 'MenuText': 'Approximate', 'ToolTip': 'Curve approximating a list of points'}

FreeCADGui.addCommand('Approximate', approx())


