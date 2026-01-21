from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any

class ExecutiveSummaryDto(BaseModel):
    # --- Datos de entrada del Repo (Excluidos del JSON final) ---
    total_studio_tracks: int = Field(0, validation_alias="total_studio_tracks", exclude=True)
    total_studio_instrumental: int = Field(0, validation_alias="total_studio_instrumental", exclude=True)
    love_songs_count: int = Field(0, validation_alias="love_songs_count", exclude=True)
    minor_keys_count: int = Field(0, validation_alias="minor_keys_count", exclude=True)
    long_studio_track_data: Optional[dict] = Field(None, exclude=True)
    short_studio_track_data: Optional[dict] = Field(None, exclude=True)

    # --- Atributos de Salida (Lo que ve el usuario) ---
    totalTracks: int = Field(0, validation_alias="total_tracks", serialization_alias="totalTracks")
    totalSongsByMusician: int = Field(0, validation_alias="total_songs_by_musician", serialization_alias="totalSongsByMusician")
    totalAlbums: int = Field(0, validation_alias="total_albums", serialization_alias="totalAlbums")
    
    # Porcentajes con aliases para camelCase
    instrumentalPercentage: float = Field(0.0, serialization_alias="instrumentalPercentage")
    loveSongsPercentage: float = Field(0.0, serialization_alias="loveSongsPercentage")
    percentageKeysMinor: float = Field(0.0, validation_alias="percentage_keys_minor", serialization_alias="percentageKeysMinor")
    
    # Strings informativos
    longStudioAlbum: str = Field("N/A", validation_alias="long_studio_album", serialization_alias="longStudioAlbum")
    shortStudioAlbum: str = Field("N/A", validation_alias="short_studio_album", serialization_alias="shortStudioAlbum")
    mostUsedKey: str = Field("N/A", validation_alias="most_used_key", serialization_alias="mostUsedKey")
    longStudioTrack: str = Field("N/A", serialization_alias="longStudioTrack")
    shortStudioTrack: str = Field("N/A", serialization_alias="shortStudioTrack")
    top1AlbumsSinger: str = Field("N/A", validation_alias="top1_albums_singer", serialization_alias="top1AlbumsSinger")

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
        if self.long_studio_track_data:
            self.longStudioTrack = f"{self.long_studio_track_data.get('title')} - {self.long_studio_track_data.get('duration')}"
        if self.short_studio_track_data:
            self.shortStudioTrack = f"{self.short_studio_track_data.get('title')} - {self.short_studio_track_data.get('duration')}"
            
        return self