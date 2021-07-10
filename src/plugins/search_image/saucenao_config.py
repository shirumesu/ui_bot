index_hmags = "1"
index_reserved = "1"
index_hcg = "1"
index_ddbobjects = "1"
index_ddbsamples = "1"
index_pixiv = "1"
index_pixivhistorical = "1"
index_reserved = "1"
index_seigaillust = "1"
index_danbooru = "1"
index_drawr = "1"
index_nijie = "1"
index_yandere = "1"
index_animeop = "1"
index_reserved = "1"
index_shutterstock = "1"
index_fakku = "1"
index_hmisc = "0"
index_2dmarket = "1"
index_medibang = "1"
index_anime = "1"
index_hanime = "1"
index_movies = "1"
index_shows = "1"
index_gelbooru = "1"
index_konachan = "1"
index_sankaku = "1"
index_animepictures = "1"
index_e621 = "1"
index_idolcomplex = "1"
index_bcyillust = "1"
index_bcycosplay = "1"
index_portalgraphics = "1"
index_da = "1"
index_pawoo = "1"
index_madokami = "1"
index_mangadex = "1"


def cal_db_bitmask():
    db_bitmask = int(
        index_mangadex
        + index_madokami
        + index_pawoo
        + index_da
        + index_portalgraphics
        + index_bcycosplay
        + index_bcyillust
        + index_idolcomplex
        + index_e621
        + index_animepictures
        + index_sankaku
        + index_konachan
        + index_gelbooru
        + index_shows
        + index_movies
        + index_hanime
        + index_anime
        + index_medibang
        + index_2dmarket
        + index_hmisc
        + index_fakku
        + index_shutterstock
        + index_reserved
        + index_animeop
        + index_yandere
        + index_nijie
        + index_drawr
        + index_danbooru
        + index_seigaillust
        + index_anime
        + index_pixivhistorical
        + index_pixiv
        + index_ddbsamples
        + index_ddbobjects
        + index_hcg
        + index_hanime
        + index_hmags,
        2,
    )
    return db_bitmask


def get_img_id(results):
    index_id = results["results"][0]["header"]["index_id"]
    data = {
        "servicename": "",
        "sim": "",
        "url": "",
        "illid": "",
        "ill_uid": "",
        "memid": "",
        "member_uid": "",
        "test_error": "no_error",
        "index_id": index_id,
        "url_for_dl": None,
    }
    if index_id == 5 or index_id == 6:
        # 5->pixiv 6->pixiv historical
        data["servicename"] = "pixiv"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["data"]["ext_urls"][0]
        data["illid"] = results["results"][0]["data"]["title"]
        data["member_uid"] = results["results"][0]["data"]["member_id"]
        data["ill_uid"] = results["results"][0]["data"]["pixiv_id"]
        data["memid"] = results["results"][0]["data"]["member_name"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 8:
        # 8->nico nico seiga
        data["servicename"] = "seiga"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["data"]["ext_urls"][0]
        data["memid"] = results["results"][0]["data"]["member_name"]
        data["illid"] = results["results"][0]["data"]["title"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 10:
        # 10->drawr
        data["servicename"] = "drawr"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["data"]["ext_urls"][0]
        data["memid"] = results["results"][0]["data"]["member_id"]
        data["illid"] = results["results"][0]["data"]["drawr_id"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 11:
        # 11->nijie
        data["servicename"] = "nijie"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["data"]["ext_urls"][0]
        data["memid"] = results["results"][0]["data"]["member_id"]
        data["illid"] = results["results"][0]["data"]["nijie_id"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 12:
        # 12->yande
        data["servicename"] = "yande"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["data"]["ext_urls"][0]
        data["memid"] = results["results"][0]["data"]["creator"]
        data["illid"] = results["results"][0]["data"]["yandere_id"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 18:
        # 18->H-Misc(nhentai)
        data["servicename"] = "H-Misc(nhentai)"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        data["memid"] = results["results"][0]["data"]["creator"][0]
        data["illid"] = results["results"][0]["data"]["source"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 21 or index_id == 22:
        # 21->anidb(番剧中确切时间)
        # 22->anidb(what anime)
        data["servicename"] = "anidb"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["data"]["ext_urls"][0]
        data["anime_name"] = results["results"][0]["data"]["source"]
        data["part"] = results["results"][0]["data"]["part"]
        data["start_time"] = (
            results["results"][0]["data"]["est_time"].split("/")[0].strip()
        )
        data["end_time"] = (
            results["results"][0]["data"]["est_time"].split("/")[1].strip()
        )
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    elif index_id == 38:
        # 38->H-Misc(E-Hentai)
        data["servicename"] = "H-Misc"
        data["sim"] = results["results"][0]["header"]["similarity"]
        data["url"] = results["results"][0]["header"]["thumbnail"]
        data["memid"] = results["results"][0]["data"]["creator"][0]
        data["illid"] = results["results"][0]["data"]["source"]
        data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
        return data

    else:
        try:
            data["servicename"] = "未知"
            data["sim"] = results["results"][0]["header"]["similarity"]
            data["url_for_dl"] = results["results"][0]["header"]["thumbnail"]
            data["illid"] = "未知"
            try:
                data["url"] = results["results"][0]["data"]["ext_urls"][0]
            except:
                data["url"] = results["results"][0]["header"]["thumbnail"]
            try:
                data["memid"] = results["results"][0]["data"]["member_id"]
            except:
                data["memid"] = "未知"
            return data

        except Exception:
            data["sim"] = results["results"][0]["header"]["similarity"]
            return data
