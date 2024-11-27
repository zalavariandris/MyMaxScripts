from typing import *
import os
import pymxs
from pathlib import Path
rt = pymxs.runtime

import os


def convert_max_to_usd(max_file_path:str|Path):
    assert str(max_file_path).lower().endswith(".max")
    max_file_path = Path(max_file_path)
    input_folder = max_file_path.parent
    output_folder = input_folder

    relative_path = max_file_path.relative_to(input_folder)
    export_path = (output_folder / relative_path).with_suffix('.usd')
    from textwrap import dedent
    print(dedent(f"""export
        {max_file_path}
        {export_path}
    """))
    
    # try:
    print(f"Opening file: {max_file_path}")
    rt.loadMaxFile(str(max_file_path.absolute()), useFileUnits=True, quite=True)
    
    export_options = rt.USDExporter.createOptions()

    export_options.Meshes = True
    export_options.Lights = False
    export_options.Cameras = False
    export_options.Materials = True
    export_options.FileFormat = rt.name('ascii')
    export_options.UpAxis = rt.name('y')
    export_options.PreserveEdgeOrientation = True
    export_options.Normals = rt.name('none')
    export_options.TimeMode = rt.name('current')

    # update the UI to match these settings:
    rt.USDexporter.UIOptions = export_options

    # export only the teapots in our list:
    result = rt.USDExporter.ExportFile(str(export_path.absolute()), contentSource=rt.Name("all"), exportOptions=export_options)
    if result:
        print('export succeeded', export_path)
    else:
        print('export failed')

source_folder = Path("C:/Users/and/Desktop/Archmodels v028 lampak/Archmodels v028")
maxfiles = list( source_folder.rglob("*.max") )
rt.setVRaySilentMode(True)
rt.SetQuietMode(True) 
for maxfile in maxfiles[:2]:
    convert_max_to_usd(maxfile)
rt.setVRaySilentMode(False)
rt.SetQuietMode(False)