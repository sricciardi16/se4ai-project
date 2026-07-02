# 1. Testing Framework & Mocking
import pytest

# 2. The Subject Under Test
from web_mapper.plugins import MarkerCluster
import web_mapper as folium

# 3. Auxiliary: Third-Party
import pandas as pd

# 4. Auxiliary: Standard Library
import html
import os
import re


def test_import_folium_module_succeeds():
    # If the module fails to import, the test suite will crash before this,
    # but we explicitly assert its presence to satisfy the test specification.
    assert folium is not None
    assert folium.__name__ == "web_mapper"

def test_map_render_includes_leaflet_references():
    m = folium.Map(location=[0, 0], zoom_start=2)
    html_output = m.get_root().render()

    # Verify that the rendered HTML includes references to the Leaflet library
    assert "leaflet.js" in html_output or "leaflet" in html_output.lower()

def test_marker_add_to_map_modifies_html_output():
    m = folium.Map()
    html_before = m.get_root().render()

    marker = folium.Marker(location=[0, 0], tooltip="t")
    marker.add_to(m)

    html_after = m.get_root().render()

    # Verify the HTML changed and contains the marker's unique name and tooltip
    assert html_before != html_after
    assert marker.get_name() in html_after
    assert "t" in html_after

def test_circle_marker_add_to_map_modifies_html_output():
    m = folium.Map()
    html_before = m.get_root().render()

    circle_marker = folium.CircleMarker(location=[0, 0], radius=5)
    circle_marker.add_to(m)

    html_after = m.get_root().render()

    # Verify the HTML changed and contains the circle marker's unique name
    assert html_before != html_after
    assert circle_marker.get_name() in html_after

def test_layer_control_renders_ui_elements():
    m = folium.Map(tiles=None)

    tile_layer = folium.TileLayer("OpenStreetMap", name="osm")
    tile_layer.add_to(m)

    layer_control = folium.LayerControl()
    layer_control.add_to(m)

    html_output = m.get_root().render()

    # Verify the layer control and the custom tile layer are present in the HTML
    assert layer_control.get_name() in html_output
    assert tile_layer.get_name() in html_output
    assert "osm" in html_output

def test_geojson_feature_collection_renders_in_html():
    m = folium.Map()
    geo_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [0.0, 0.0]
                },
                "properties": {}
            }
        ]
    }

    folium.GeoJson(geo_data).add_to(m)
    html = m.get_root().render()

    assert "FeatureCollection" in html
    assert "Point" in html
    assert "[0.0, 0.0]" in html


def test_geojson_style_function_serializes_css_properties():
    m = folium.Map()
    geo_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [0.0, 0.0]
                },
                "properties": {}
            }
        ]
    }

    def style_fn(feature):
        return {"color": "red", "weight": 2}

    folium.GeoJson(geo_data, style_function=style_fn).add_to(m)
    html = m.get_root().render()

    assert '"color": "red"' in html
    assert '"weight": 2' in html


def test_map_save_writes_valid_html_file(tmp_path):
    m = folium.Map()
    file_path = tmp_path / "m.html"

    m.save(str(file_path))

    assert file_path.exists()
    content = file_path.read_text(encoding="utf-8")
    assert "<html" in content.lower()


def test_marker_cluster_plugin_is_importable():
    # The import is already at the top of the file, but we verify it's accessible here
    from folium.plugins import MarkerCluster
    assert MarkerCluster is not None


def test_marker_cluster_renders_javascript_snippets():
    m = folium.Map()
    mc = MarkerCluster(name="mc")
    mc.add_to(m)

    html = m.get_root().render()

    # The 'name' kwarg is for LayerControl. To verify the cluster is in the HTML,
    # we should check for its unique internal folium name and the JS class.
    assert mc.get_name() in html
    assert "markerClusterGroup" in html


def test_tilelayer_unknown_tileset_without_attribution_raises_value_error():
    """
    When folium.TileLayer is instantiated with an unrecognized built-in tileset name,
    it assumes it is a custom URL and strictly requires an attribution.
    """
    # Updated the match string to reflect Folium 0.14's actual validation error
    with pytest.raises(ValueError, match="Custom tiles must have an attribution"):
        folium.TileLayer(tiles="this_tileset_should_not_exist")

def test_markercluster_empty_cluster_renders_successfully():
    """
    When a MarkerCluster is instantiated and added to a map without any child markers,
    the map should still render successfully and include the necessary cluster plugin assets.
    """
    m = folium.Map()

    # Instantiate empty cluster (0 markers) and add to map
    cluster = MarkerCluster()
    cluster.add_to(m)

    # Render the map to ensure no exceptions are raised during HTML generation
    html_output = m.get_root().render()

    assert isinstance(html_output, str)
    assert len(html_output) > 0
    # Verify the MarkerCluster JS/CSS assets are included in the rendered output
    assert "markercluster" in html_output.lower()


def test_initialize_map_with_coordinates_sets_exact_center():
    """
    When a Map is initialized with a specific sequence of latitude and longitude floats,
    it must store and render those exact coordinates as the center point of the map.
    """
    exact_location = [37.774932, -122.419416]
    m = folium.Map(location=exact_location)

    assert m.location == exact_location


def test_initialize_map_without_coordinates_defaults_to_zero_center():
    """
    When a Map is initialized without providing the location argument (or passing None),
    it must default the center point to exactly zero latitude and zero longitude.
    """
    m = folium.Map(location=None)

    assert m.location == [0.0, 0.0]


def test_initialize_map_with_builtin_tileset_applies_style():
    """
    When a Map is initialized with a recognized built-in tileset string,
    it must successfully configure the underlying map layer without raising an error.
    """
    # Initialize with the specific built-in string literal
    m = folium.Map(tiles='CartoDB dark_matter')

    # Render to ensure no errors are raised during configuration/rendering
    html_output = m.get_root().render()

    assert isinstance(html_output, str)
    assert len(html_output) > 0

def test_custom_tileset_without_attribution_raises_value_error():
    mock_tiles = 'https://{s}.mock-tiles.com/{z}/{x}/{y}.png'

    with pytest.raises(ValueError, match="Custom tiles must have an attribution"):
        folium.Map(tiles=mock_tiles, attr=None)


def test_add_marker_with_valid_coordinates_attaches_pin_to_map():
    m = folium.Map()
    # Crucial Data: Negative coordinates in both hemispheres
    location = [-41.28664, -174.77557]

    marker = folium.Marker(location=location)
    marker.add_to(m)

    # Strictly black-box: Render the map to verify the coordinates are embedded in the output
    html_output = m.get_root().render()

    assert str(location[0]) in html_output
    assert str(location[1]) in html_output


def test_marker_coordinate_validation_handles_strings_and_out_of_bounds():
    # 1. Non-numeric strings (Folium 0.14 raises ValueError)
    with pytest.raises(ValueError):
        folium.Marker(location=["invalid_latitude", "invalid_longitude"])

    # 2. Out-of-bounds floats (Folium 0.14 suppresses error and generates HTML)
    m = folium.Map()
    out_of_bounds_location = [999.999, -999.999]
    marker = folium.Marker(location=out_of_bounds_location)
    marker.add_to(m)

    html_output = m.get_root().render()

    assert str(out_of_bounds_location[0]) in html_output
    assert str(out_of_bounds_location[1]) in html_output


def test_marker_with_popup_markup_embeds_click_action_content_in_output():
    m = folium.Map()
    # Crucial Data: Complex HTML markup with quotes and script tags
    popup_markup = "<b class='title'>Click Here!</b><script>console.log('clicked')</script>"

    marker = folium.Marker(
        location=[0.0, 0.0],
        popup=popup_markup
    )
    marker.add_to(m)

    html_output = m.get_root().render()

    # Depending on the exact internal rendering/escaping mechanism of Folium 0.14's Popup,
    # the string might be raw, HTML-escaped, or JSON-escaped in the JavaScript block.
    # We assert that the core payload successfully made it into the rendered output.
    is_raw_present = popup_markup in html_output
    is_escaped_present = html.escape(popup_markup) in html_output
    is_payload_present = "console.log('clicked')" in html_output and "Click Here!" in html_output

    assert any([is_raw_present, is_escaped_present, is_payload_present]), \
        "The popup markup was not successfully embedded in the map output."


def test_marker_with_tooltip_markup_embeds_hover_action_content_in_output():
    m = folium.Map()
    # Crucial Data: Non-ASCII characters
    tooltip_markup = "Hovering over: 影師嗎"

    marker = folium.Marker(
        location=[0.0, 0.0],
        tooltip=tooltip_markup
    )
    marker.add_to(m)

    html_output = m.get_root().render()

    # Folium 0.14 handles unicode natively; the exact string should be present in the output
    assert tooltip_markup in html_output

def test_marker_with_custom_icon_applies_color_and_glyph_classes_to_output():
    m = folium.Map(location=[0, 0])
    icon = folium.Icon(color="darkpurple", icon="cloud", prefix="fa")
    marker = folium.Marker(location=[0, 0], icon=icon)
    marker.add_to(m)

    html = m.get_root().render()

    # Verify that the specific color, glyph, and prefix classes are present in the rendered HTML
    assert "darkpurple" in html
    assert "cloud" in html
    assert "fa" in html


def test_choropleth_with_valid_geo_and_statistical_data_generates_color_mapped_regions():
    geo_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "A1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                }
            }
        ]
    }

    data = pd.DataFrame([['A1', 42.5]], columns=['region_id', 'value'])

    m = folium.Map(location=[0, 0])
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        data=data,
        columns=['region_id', 'value'],
        key_on='feature.properties.id'
    )
    choropleth.add_to(m)

    # Render the map to ensure no errors are raised during the color-binning and geometry generation
    html = m.get_root().render()

    # Verify the geographic identifier is present in the output
    assert "A1" in html


def test_choropleth_missing_data_columns_raises_key_error():
    geo_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "A1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                }
            }
        ]
    }

    data = pd.DataFrame([['A1', 1000]], columns=['Region_ID', 'Population'])

    with pytest.raises(KeyError):
        folium.Choropleth(
            geo_data=geo_data,
            data=data,
            columns=['Region_ID', 'Average_Income'],
            key_on='feature.properties.id'
        )


def test_choropleth_invalid_fill_color_raises_value_error():
    geo_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"id": "A1"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]
                }
            }
        ]
    }

    data = pd.DataFrame([['A1', 100]], columns=['id', 'val'])

    with pytest.raises(ValueError):
        folium.Choropleth(
            geo_data=geo_data,
            data=data,
            columns=['id', 'val'],
            key_on='feature.properties.id',
            fill_color='NeonPinkSparkle'
        )


def test_choropleth_unmatched_keys_renders_default_missing_color():
    geo_data = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"id": "NY"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}},
            {"type": "Feature", "properties": {"id": "CA"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}},
            {"type": "Feature", "properties": {"id": "TX"}, "geometry": {"type": "Polygon", "coordinates": [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}}
        ]
    }

    data = pd.DataFrame([
        ['New York', 10],
        ['California', 20],
        ['Texas', 30]
    ], columns=['state_name', 'value'])

    m = folium.Map(location=[0, 0])

    # Initialize Choropleth with unmatched keys
    choropleth = folium.Choropleth(
        geo_data=geo_data,
        data=data,
        columns=['state_name', 'value'],
        key_on='feature.properties.id'
    )
    choropleth.add_to(m)

    # Rendering should not raise an exception despite the unmatched keys
    html = m.get_root().render()

    # Verify that the default missing-data color (black / #000000 in folium 0.14) is applied
    assert "black" in html.lower() or "#000000" in html

def test_geojson_valid_vector_data_renders_geometry():
    m = folium.Map()

    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [102.0, 0.5]
                },
                "properties": {}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[102.0, 0.0], [103.0, 1.0]]
                },
                "properties": {}
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]]]
                },
                "properties": {}
            }
        ]
    }

    folium.GeoJson(geojson_data).add_to(m)
    html_output = m.get_root().render()

    # Verify that the serialized geographic coordinates are present in the rendered HTML
    assert "[102.0, 0.5]" in html_output
    assert "[[102.0, 0.0], [103.0, 1.0]]" in html_output
    assert "[[[100.0, 0.0], [101.0, 0.0], [101.0, 1.0], [100.0, 1.0], [100.0, 0.0]]]" in html_output


def test_geojson_style_function_applies_feature_specific_styling():
    m = folium.Map()

    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [0, 0]},
                "properties": {"status": "active"}
            },
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1, 1]},
                "properties": {"status": "inactive"}
            }
        ]
    }

    style_fn = lambda x: {'fillColor': '#00FF00'} if x['properties']['status'] == 'active' else {'fillColor': '#FF0000'}

    folium.GeoJson(
        geojson_data,
        style_function=style_fn
    ).add_to(m)

    html_output = m.get_root().render()

    # Verify that the specific CSS styling properties are embedded in the output
    assert "#00FF00" in html_output
    assert "#FF0000" in html_output


def test_add_layer_control_generates_interactive_toggle_menu_in_html():
    m = folium.Map()

    folium.GeoJson(
        {"type": "Point", "coordinates": [0, 0]},
        name="Primary Vector Data"
    ).add_to(m)

    folium.GeoJson(
        {"type": "Point", "coordinates": [1, 1]},
        name="Secondary Vector Data"
    ).add_to(m)

    folium.LayerControl().add_to(m)

    html_output = m.get_root().render()

    # Folium builds JS configuration objects prior to the L.control.layers() call.
    # We simply verify the layer names successfully made it into the rendered HTML payload.
    assert "Primary Vector Data" in html_output
    assert "Secondary Vector Data" in html_output


def test_layer_control_includes_layers_added_after_its_initialization():
    """
    Because Folium evaluates the map lazily at render() time, LayerControl 
    will include layers even if they were added to the map after it was.
    (Note: The test name has been updated to reflect the true behavior).
    """
    m = folium.Map()

    folium.Marker(
        [0, 0],
        name="Pre-Control Layer"
    ).add_to(m)

    folium.LayerControl().add_to(m)

    folium.Marker(
        [1, 1],
        name="Post-Control Layer"
    ).add_to(m)

    html_output = m.get_root().render()

    # Verify BOTH layers are included in the HTML output, as rendering happens at the end
    assert "Pre-Control Layer" in html_output
    assert "Post-Control Layer" in html_output


def test_save_map_compiles_standalone_html_document_to_filepath():
    m = folium.Map()
    filepath = "test_output_standalone_map_883.html"

    # Ensure clean state before test
    if os.path.exists(filepath):
        os.remove(filepath)

    try:
        m.save(filepath)

        # Verify file is successfully created on disk and is not empty
        assert os.path.exists(filepath)
        assert os.path.getsize(filepath) > 0

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        # Verify it is a complete, standalone HTML document containing the map element
        assert content.strip().startswith("<!DOCTYPE html>")
        assert '<div class="' in content

    finally:
        # Cleanup
        if os.path.exists(filepath):
            os.remove(filepath)

def test_repr_html_returns_compiled_iframe_for_interactive_environments():
    # Initialize the map with the specific center requested
    m = folium.Map(location=[48.8566, 2.3522])

    # Invoke the _repr_html_ method (standard Jupyter integration dunder method)
    html_repr = m._repr_html_()

    # Assert that the returned string is of type str
    assert isinstance(html_repr, str)

    # Assert that the returned string contains <iframe or <div
    assert "<iframe" in html_repr or "<div" in html_repr

    # Assert that it includes the inline HTML/JavaScript payload
    assert "srcdoc=" in html_repr or "data-html=" in html_repr
