# -*- coding: utf-8 -*-
"""
Created on Mon Nov 13 21:37:02 2017

@author: CTremblay
"""

def create_sidebar():
    sb = """
    	<div class="wrapper">
    <div class="sidebar" data-background-color="white" data-active-color="danger">

    <!--
		Tip 1: you can change the color of the sidebar's background using: data-background-color="white | black"
		Tip 2: you can change the color of the active button using the data-active-color="primary | info | success | warning | danger"
	-->

    	<div class="sidebar-wrapper">
            <div class="logo">
                <a href="http://www.creative-tim.com" class="simple-text">
                    BAC0
                </a>
            </div>

            <ul class="nav">
                <li class="active">
                    <a href="/dash">
                        <i class="ti-panel"></i>
                        <p>Dashboard</p>
                    </a>
                </li>
                <li>
                    <a href="/dash_devices">
                        <i class="ti-view-list-alt"></i>
                        <p>Devices</p>
                    </a>
                </li>
            </ul>
    	</div>
    </div>
    """
    return sb

def create_card(icon = 'ti-server', title = 'title', data = 'None', name = '#name', foot_icon = 'ti-reload', foot_data = 'None'):
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
                            <div name = "%s">%s</div>
                        </div>
                    </div>
                </div>
                <div class="footer">
                    <hr />
                    <div class="stats">
                        <i class="%s"></i> %s
                    </div>
                </div>
            </div>
        </div>
        </div>
        """ % (icon, title, name, data, foot_icon, foot_data)
    return card