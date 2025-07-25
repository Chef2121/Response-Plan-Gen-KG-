"""Database schema documentation."""

schema_docs = """
    Link nodes represent segments of the road 
    The Link node have the following properties
    from_junction, string, the junction where the link starts from
    link_id, string, the unique id for the link
    meters, string, the length of the link in meters
    to_junction, string, the junction where the link ends at

    VMS nodes represent electronic warning signs on the road
    The VMS nodes have the following properties
    DIST_TO_UPNODE, integer, distance in meters to the up node
    EQT_EXT_ID, string, the equipment unique id number
    EQT_NO, string, the equipment unique id number
    EQT_TYPE, string, the type of equipment
    ID, integer, 3-digit id of equipment
    LATITUDE, float, latitude position of equipment
    LINK_ID, integer, unique id of link where equipment is positioned
    LONGITUDE, float, longitude position of equipment
    ROAD_CAT, string, category of road equipment is placed at
    ROAD_CODE, string, code of road equipment is placed at
    ROAD_NAME, string, name of road equipment is placed at

    RELATIONSHIPS:
    The Link node and VMS node are connected by relationship LOCATED_AT which indicates where the VMS is located at it is always VMS to Link.
    They are connected by matching identical VMS (LINK_ID) to Link (link_id),
    when matching ensure for VMS it is an integer and for Link it is a string

    The Link nodes are connected by relationship CONNECTED_TO which represents the physical road network topology.
    CONNECTED_TO relationships form bidirectional connections between adjacent road segments.
    Links are connected by matching Link (to_junction) with Link (from_junction) of adjacent segments.
"""
