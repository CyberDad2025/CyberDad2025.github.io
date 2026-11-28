#!/usr/bin/env ruby
# Render _includes/what-buyers-say.html with a YAML data payload.
# Usage: ruby tests/render_what_buyers_say.rb DATA.yml INCLUDE.html
require "liquid"
require "yaml"
data = YAML.safe_load(File.read(ARGV[0]))
data = [] if data.nil?
tmpl = File.read(ARGV[1])
print Liquid::Template.parse(tmpl).render("site" => {"data" => {"what_buyers_say" => data}})
