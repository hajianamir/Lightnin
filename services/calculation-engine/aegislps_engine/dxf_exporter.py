import ezdxf
import io

class DXFExporter:
    @staticmethod
    def export_2d_plan(building_length: float, building_width: float, nodes: list) -> bytes:
        doc = ezdxf.new(dxfversion="R2010")
        msp = doc.modelspace()

        # Add layers using valid ezdxf API
        layer_bldg = doc.layers.add("BUILDING_OUTLINE")
        layer_bldg.color = 7

        layer_air = doc.layers.add("AIR_TERMINATIONS")
        layer_air.color = 1 # Red

        # Draw Building Box
        msp.add_lwpolyline([
            (0, 0),
            (building_length, 0),
            (building_length, building_width),
            (0, building_width),
            (0, 0)
        ], dxfattribs={"layer": "BUILDING_OUTLINE"})

        # Draw Air Termination Nodes
        for n in nodes:
            msp.add_circle((n.get("x", 0), n.get("y", 0)), radius=0.3, dxfattribs={"layer": "AIR_TERMINATIONS"})

        stream = io.StringIO()
        doc.write(stream)
        return stream.getvalue().encode('utf-8')
