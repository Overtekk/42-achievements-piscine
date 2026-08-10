require "oauth2"
require "json"

UID = "u-s4t2ud-b132035c6f0f20764c43b0b387d51ec97781e209989a8be7c89960514232a2bb"
SECRET = "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"
CAMPUS_ID = 62   # Le Havre
CURSUS_ID = 9    # C Piscine

def request(token, path)
  3.times do
    begin
      return token.get(path)
    rescue OAuth2::Error => e
      raise unless e.response.status == 429
      sleep 1
    end
  end
  raise "rate limited"
end

def fetch_all(token, path)
  items = []
  page = 1
  loop do
    body = request(token, "#{path}#{path.include?("?") ? "&" : "?"}page[size]=100&page[number]=#{page}").body
    chunk = JSON.parse(body)
    break if chunk.empty?
    items.concat(chunk)
    page += 1
    sleep 0.1
  end
  items
end

def trim_cache(max = 5)
  caches = Dir.glob(File.join(__dir__, "cache_projects_users_*.json")).sort_by { |f| File.mtime(f) }
  while caches.size > max
    oldest = caches.shift
    puts "removing old cache: #{File.basename(oldest)}"
    File.delete(oldest)
  end
end

def cached_fetch(token, path, cache_file)
  if File.exist?(cache_file)
    data = JSON.parse(File.read(cache_file))
    puts "cache hit: #{File.basename(cache_file)} (#{data.size} items)"
    return data
  end
  data = fetch_all(token, path)
  File.write(cache_file, JSON.generate(data))
  trim_cache
  data
end

client = OAuth2::Client.new(UID, SECRET, site: "https://api.intra.42.fr")
token = client.client_credentials.get_token

from = (Time.now - 3600).utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")
to = Time.now.utc.strftime("%Y-%m-%dT%H:%M:%S.000Z")

piscine = cached_fetch(token, "/v2/cursus/#{CURSUS_ID}/projects", "/home/oxy/42-achievements-piscine/cache_projects.json")
piscine_ids = piscine
  .select { |p| p["campus"].any? { |c| c["id"] == CAMPUS_ID } }
  .map { |p| p["id"] }
puts "C Piscine projects at Le Havre: #{piscine_ids.size}"

records = cached_fetch(token,
  "/v2/projects_users?filter[campus]=#{CAMPUS_ID}&filter[status]=finished&range[marked_at]=#{from},#{to}",
  "/home/oxy/42-achievements-piscine/cache_projects_users_#{from}.json")
puts "finished projects_users (campus #{CAMPUS_ID}): #{records.size}"

succeeded = records.select { |r| piscine_ids.include?(r["project"]["id"]) && r["validated?"] }

by_project = succeeded.group_by { |r| r["project"]["name"] }
by_project.each_value { |rs| rs.map! { |r| r["user"]["login"] }.sort! { |a, b| a.downcase <=> b.downcase } }

output = by_project.sort_by { |name, _| name }.to_h
File.write("/home/oxy/42-achievements-piscine/piscine.json", JSON.pretty_generate(output))
puts "Wrote piscine.json (#{by_project.size} projects)"

puts "\n#{succeeded.group_by { |r| r["user"]["login"] }.size} user(s) validated C Piscine project(s) at Le Havre"

