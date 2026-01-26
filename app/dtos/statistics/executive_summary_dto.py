from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any

class ExecutiveSummaryDto(BaseModel):
    # --- Datos de entrada del Repo (Excluidos del JSON final) ---
    total_studio_tracks: int = Field(0, validation_alias="total_studio_tracks", exclude=True)
    total_studio_instrumental: int = Field(0, validation_alias="total_studio_instrumental", exclude=True)
    love_songs_count: int = Field(0, validation_alias="love_songs_count", exclude=True)
    minor_keys_count: int = Field(0, validation_alias="minor_keys_count", exclude=True)
    longest_studio_track_data: Optional[dict] = Field(None, exclude=True)
    shortest_studio_track_data: Optional[dict] = Field(None, exclude=True)

    # --- Atributos de Salida (Lo que ve el usuario) ---
    totalTracks: int = Field(0, validation_alias="total_tracks", serialization_alias="totalTracks")
    totalSongsByMusician: int = Field(0, validation_alias="total_songs_by_musician", serialization_alias="totalSongsByMusician")
    totalAlbums: int = Field(0, validation_alias="total_albums", serialization_alias="totalAlbums")
    totalAlbumsWithoutInstrumentals: int = Field(0, validation_alias="count_albums_without_instrumentals", serialization_alias="totalAlbumsWithoutInstrumentals")
    totalGuestArtists: int = Field(0, validation_alias="total_guest_artists", serialization_alias="totalGuestArtists")
    totalLiveTracksInStudioAlbums: int = Field(0,validation_alias="total_live_tracks_in_studio_albums", serialization_alias="totalLiveTracksInStudioAlbums")
    totalTracksCarlosComposer: int = Field(0,validation_alias="total_tracks_carlos_composer", serialization_alias="totalTracksCarlosComposer")

    # Porcentajes con aliases para camelCase
    instrumentalPercentage: float = Field(0.0, serialization_alias="instrumentalPercentage")
    loveSongsPercentage: float = Field(0.0, serialization_alias="loveSongsPercentage")
    percentageKeysMinor: float = Field(0.0, validation_alias="percentage_keys_minor", serialization_alias="percentageKeysMinor")
    
    # Strings informativos
    longestStudioAlbum: str = Field("N/A", validation_alias="longest_studio_album", serialization_alias="longestStudioAlbum")
    shortestStudioAlbum: str = Field("N/A", validation_alias="shortest_studio_album", serialization_alias="shortestStudioAlbum")
    mostUsedKey: str = Field("N/A", validation_alias="most_used_key", serialization_alias="mostUsedKey")
    longestStudioTrack: str = Field("N/A", serialization_alias="longestStudioTrack")
    shortestStudioTrack: str = Field("N/A", serialization_alias="shortestStudioTrack")
    top1AlbumsSinger: str = Field("N/A", validation_alias="top1_albums_singer", serialization_alias="top1AlbumsSinger")
    mostInstrumentalAlbum: str = Field("N/A", validation_alias="most_instrumental_album", serialization_alias="mostInstrumentalAlbum")

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    @model_validator(mode="after")
    def finalize_and_round_stats(self) -> "ExecutiveSummaryDto":
        """
        Orquestador de cálculos y redondeos finales.
        """
        # 1. Porcentaje Instrumental (Lógica Invertida: STUDIO)
        if self.total_studio_tracks > 0:
            self.instrumentalPercentage = round((self.total_studio_instrumental * 100) / self.total_studio_tracks, 2)
        
        # 2. Porcentaje de Love Songs (Global)
        if self.totalTracks > 0:
            self.loveSongsPercentage = round((self.love_songs_count * 100) / self.totalTracks, 2)
        
        # 3. Redondeo de Percentage Keys Minor (Si viene de Mongo)
        # Lo redondeamos por si acaso el cálculo en Mongo trajo muchos decimales
        self.percentageKeysMinor = round(self.percentageKeysMinor, 2)
        
        # 4. Formateo de nombres de canciones (Solo Live tracks)
        if self.longest_studio_track_data:
            self.longestStudioTrack = f"{self.longest_studio_track_data.get('title')} - {self.longest_studio_track_data.get('duration')}"
        if self.shortest_studio_track_data:
            self.shortestStudioTrack = f"{self.shortest_studio_track_data.get('title')} - {self.shortest_studio_track_data.get('duration')}"
            
        return self