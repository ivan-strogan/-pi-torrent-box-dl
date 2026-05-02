<?php
class SynoDLMSearch1337xJackett {
    private $jackett_url = 'http://192.168.0.6:9117';
    private $api_key = '0dhutx0dofdrjcscx29ni6xt8cne5c5t';
    private $indexer = '1337x';

    public function prepare($curl, $query) {
        $url = sprintf(
            '%s/api/v2.0/indexers/%s/results/torznab/?apikey=%s&t=search&q=%s',
            $this->jackett_url,
            $this->indexer,
            $this->api_key,
            urlencode($query)
        );
        curl_setopt($curl, CURLOPT_URL, $url);
    }

    public function parse($plugin, $response) {
        $res = 0;

        $xml = simplexml_load_string($response);
        if (!$xml) return $res;

        $ns = $xml->getNamespaces(true);
        $torznab_ns = isset($ns['torznab']) ? $ns['torznab'] : 'http://torznab.com/schemas/2015/feed';

        foreach ($xml->channel->item as $item) {
            $title    = (string)$item->title;
            $link     = (string)$item->link;
            $size     = (int)$item->size;
            $pub_date = (string)$item->pubDate;
            $guid     = (string)$item->guid;

            $seeds    = 0;
            $leechs   = 0;
            $magnet   = '';
            $category = 'Other';

            foreach ($item->children($torznab_ns) as $attr) {
                $name  = (string)$attr['name'];
                $value = (string)$attr['value'];
                if ($name === 'seeders')   $seeds  = (int)$value;
                elseif ($name === 'leechers') $leechs = (int)$value;
                elseif ($name === 'magneturl') $magnet = $value;
                elseif ($name === 'genre')    $category = $value;
            }

            $download = $magnet ? $magnet : $link;
            $hash     = md5($guid . $title);
            $datetime = $pub_date ? date('Y-m-d H:i', strtotime($pub_date)) : date('Y-m-d H:i');

            if ($title && $download) {
                $plugin->addResult($title, $download, $size, $datetime, 'https://1337x.to', $hash, $seeds, $leechs, $category);
                $res++;
            }
        }

        return $res;
    }
}
?>
