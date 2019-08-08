# -*- coding: utf-8 -*-
"""
Created on Mon Nov 13 21:37:02 2017

@author: CTremblay
"""


def create_sidebar(dash_class="", devices_class="", trends_class=""):
    sb = """
    <div class="wrapper">
    <div class="sidebar" data-background-color="white" data-active-color="danger">
    <!--
    Tip 1: you can change the color of the sidebar's background using: data-background-color="white | black"
    Tip 2: you can change the color of the active button using the data-active-color="primary | info | success | warning | danger"
    -->
    <div class="sidebar-wrapper">
      <div class="logo">
      <a href="https://github.com/ChristianTremblay/BAC0" class="simple-text">BAC0</a>
      </div>
      <ul class="nav">
        <li {}><a href="/">
               <i class="ti-panel"></i>
               <p>Dashboard</p>
               </a>
        </li>
        <li {}><a href="/trends">
               <i class="ti-panel"></i>
               <p>Trend</p>
               </a>
        </li>
        <li {}><a href="/dash_devices">
               <i class="ti-view-list-alt"></i>
               <p>Devices</p>
               </a>
        </li>
      </ul>
      </div>
    </div>
    """.format(
        dash_class, trends_class, devices_class
    )
    return sb


def update_notifications(log, new_msg):
    notif_log = log
    max_notifications = 5
    if new_msg:
        notif_log.insert(0, new_msg)
    if len(notif_log) > max_notifications:
        notif_log.pop()

    notif_list = '<ul class="dropdown-menu">'
    for notif in notif_log:
        notif_list += '<li><a href="#">' + notif + "</a></li>"
    if len(notif_log) == 0:
        notif_list += '<li><a href="#">Nothing yet</a></li>'
    notif_list += "</ul>"
    return notif_list


def create_card(
    icon="ti-server",
    title="title",
    data="None",
    id_data="generic_data",
    foot_icon="ti-reload",
    foot_data="None",
    id_foot_data="generic_foot_data",
):
    card = """
        <div class="col-lg-3 col-sm-6">
        <div class="card">
          <div class="content">
            <div class="row">
              <div class="col-xs-5">
                <div class="icon-big icon-success text-center">
                  <i class="{}"></i>
                </div>
              </div>
                <div class="col-xs-7">
                  <div class="numbers">
                    <p>{}</p>
                    <div id="{}">{}</div>
                  </div>
                </div>
              </div>
            <div class="footer">
            <hr />
            <div class="stats">
            <i class="{}"></i> <div id="{}">{}</div>
            </div>
            </div>
            </div>
        </div>
        </div>
        """.format(
        icon, title, id_data, data, foot_icon, id_foot_data, foot_data
    )
    return card
