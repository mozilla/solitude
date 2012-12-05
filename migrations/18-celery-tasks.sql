-- This is a straight dump of:
-- ./manage.py sqlreset djcelery
CREATE TABLE `celery_taskmeta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `task_id` varchar(255) NOT NULL UNIQUE,
    `status` varchar(50) NOT NULL,
    `result` longtext,
    `date_done` datetime NOT NULL,
    `traceback` longtext
)
;
CREATE TABLE `celery_tasksetmeta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `taskset_id` varchar(255) NOT NULL UNIQUE,
    `result` longtext NOT NULL,
    `date_done` datetime NOT NULL
)
;
CREATE TABLE `djcelery_intervalschedule` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `every` integer NOT NULL,
    `period` varchar(24) NOT NULL
)
;
CREATE TABLE `djcelery_crontabschedule` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `minute` varchar(64) NOT NULL,
    `hour` varchar(64) NOT NULL,
    `day_of_week` varchar(64) NOT NULL
)
;
CREATE TABLE `djcelery_periodictasks` (
    `ident` smallint NOT NULL PRIMARY KEY,
    `last_update` datetime NOT NULL
)
;
CREATE TABLE `djcelery_periodictask` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(200) NOT NULL UNIQUE,
    `task` varchar(200) NOT NULL,
    `interval_id` integer,
    `crontab_id` integer,
    `args` longtext NOT NULL,
    `kwargs` longtext NOT NULL,
    `queue` varchar(200),
    `exchange` varchar(200),
    `routing_key` varchar(200),
    `expires` datetime,
    `enabled` bool NOT NULL,
    `last_run_at` datetime,
    `total_run_count` integer UNSIGNED NOT NULL,
    `date_changed` datetime NOT NULL
)
;
ALTER TABLE `djcelery_periodictask` ADD CONSTRAINT `interval_id_refs_id_f2054349` FOREIGN KEY (`interval_id`) REFERENCES `djcelery_intervalschedule` (`id`);
ALTER TABLE `djcelery_periodictask` ADD CONSTRAINT `crontab_id_refs_id_ebff5e74` FOREIGN KEY (`crontab_id`) REFERENCES `djcelery_crontabschedule` (`id`);
CREATE TABLE `djcelery_workerstate` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `hostname` varchar(255) NOT NULL UNIQUE,
    `last_heartbeat` datetime
)
;
CREATE TABLE `djcelery_taskstate` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `state` varchar(64) NOT NULL,
    `task_id` varchar(36) NOT NULL UNIQUE,
    `name` varchar(200),
    `tstamp` datetime NOT NULL,
    `args` longtext,
    `kwargs` longtext,
    `eta` datetime,
    `expires` datetime,
    `result` longtext,
    `traceback` longtext,
    `runtime` double precision,
    `worker_id` integer,
    `hidden` bool NOT NULL
)
;
ALTER TABLE `djcelery_taskstate` ADD CONSTRAINT `worker_id_refs_id_4e3453a` FOREIGN KEY (`worker_id`) REFERENCES `djcelery_workerstate` (`id`);
CREATE INDEX `djcelery_periodictask_17d2d99d` ON `djcelery_periodictask` (`interval_id`);
CREATE INDEX `djcelery_periodictask_7aa5fda` ON `djcelery_periodictask` (`crontab_id`);
CREATE INDEX `djcelery_workerstate_eb8ac7e4` ON `djcelery_workerstate` (`last_heartbeat`);
CREATE INDEX `djcelery_taskstate_355bfc27` ON `djcelery_taskstate` (`state`);
CREATE INDEX `djcelery_taskstate_52094d6e` ON `djcelery_taskstate` (`name`);
CREATE INDEX `djcelery_taskstate_f0ba6500` ON `djcelery_taskstate` (`tstamp`);
CREATE INDEX `djcelery_taskstate_20fc5b84` ON `djcelery_taskstate` (`worker_id`);
CREATE INDEX `djcelery_taskstate_c91f1bf` ON `djcelery_taskstate` (`hidden`);
