# -*- coding: utf-8 -*-
"""
Created on Mon Nov 13 21:37:02 2017

@author: CTremblay
"""

def create_sidebar(dash_class = "", devices_class = "", trends_class = ""):
    sb = """
    	<div class="wrapper">
    <div class="sidebar" data-background-color="white" data-active-color="danger">

    <!--
		Tip 1: you can change the color of the sidebar's background using: data-background-color="white | black"
		Tip 2: you can change the color of the active button using the data-active-color="primary | info | success | warning | danger"
	-->

    	<div class="sidebar-wrapper">
            <div class="logo">
                <a href="https://github.com/ChristianTremblay/BAC0" class="simple-text">
                    BAC0
                </a>
            </div>

            <ul class="nav">
                <li %s>
                    <a href="/">
                        <i class="ti-panel"></i>
                        <p>Dashboard</p>
                    </a>
                </li>
                <li %s>
                    <a href="/trends">
                        <i class="ti-panel"></i>
                        <p>Trend</p>
                    </a>
                </li>
                <li %s>
                    <a href="/dash_devices">
                        <i class="ti-view-list-alt"></i>
                        <p>Devices</p>
                    </a>
                </li>
            </ul>
    	</div>
    </div>
    """ % (dash_class, trends_class, devices_class)
    return sb

def create_card(icon = 'ti-server', title = 'title', 
                data = 'None', id_data = 'generic_data',  
                foot_icon = 'ti-reload', foot_data = 'None', id_foot_data = 'generic_foot_data'):
    card = """
        <div class="col-lg-3 col-sm-6">
        <div class="card">
            <div class="content">
                <div class="row">
                    <div class="col-xs-5">
                        <div class="icon-big icon-success text-center">
                            <i class="%s"></i>
                        </div>
                    </div>
                    <div class="col-xs-7">
                        <div class="numbers">
                            <p>%s</p>
                            <div id="%s">%s</div>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    <hr />
                    <div class="stats">
                        <i class="%s"></i> <div id="%s">%s</div>
                    </div>
                </div>
            </div>
        </div>
        </div>
        """ % (icon, title, id_data, data, foot_icon, id_foot_data, foot_data)
    return card