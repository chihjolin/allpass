SHOW VARIABLES LIKE 'secure_file_priv';

use titanic_db;
select * from passengers;

create database if not exists allpass;
show databases;


use allpass;
create table trail(
id varchar(50) primary key,
name varchar(100),
location varchar(100),
difficulty ENUM('L','M','H'),
permit_required boolean,
planningPageUrl varchar(100),
totalTime varchar(50),
distance varchar(50),
ascent varchar(50),
descent varchar(50),
weatherStation_id varchar(50)
);

create table trail_stats();

create table weatherStation(
id int primary key,
locationName varchar(50));





